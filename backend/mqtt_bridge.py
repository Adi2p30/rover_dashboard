"""Bridges the synchronous paho-mqtt client into the asyncio world: paho's network
thread pushes incoming messages into an asyncio.Queue (via call_soon_threadsafe),
and a background asyncio task drains that queue to update state, run fault
detection, and broadcast to connected WebSocket clients."""
from __future__ import annotations

import asyncio
import json
import time

import paho.mqtt.client as mqtt

from backend.alerting.alert_manager import AlertManager
from backend.alerting.safe_state import SafeStatePublisher
from backend.config import (
    LOG_TOPIC_PREFIX,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_SUBSCRIBE_TOPIC,
    ROS2_CAMERA_TOPIC,
    ROS2_SIM_TOPICS,
)
from backend.fault_detection.registry import DetectorRegistry
from backend.ros2_translate import translate
from backend.state_store import StateStore, topic_to_point_id

STALENESS_POLL_INTERVAL = 1.0


class MQTTBridge:
    def __init__(self, broadcast_fn):
        """broadcast_fn(dict) -- coroutine or sync callable that sends a JSON-able
        frame to every connected WebSocket client."""
        self.state_store = StateStore()
        self.registry = DetectorRegistry()
        self.alert_manager = AlertManager(on_safe_state_change=self._on_safe_state_change)
        self.safe_state = SafeStatePublisher(publish_fn=self._publish)
        self._broadcast_fn = broadcast_fn

        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="rover-backend")
        self._client.on_message = self._on_message
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        self._rx_count = 0
        self._tx_count = 0
        self._last_topic = ""

    # --- paho callbacks (run on paho's network thread) ---

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        print(f"[backend] connected to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} "
              f"(reason={reason_code}), subscribing to '{MQTT_SUBSCRIBE_TOPIC}' and ros2_sim topics {ROS2_SIM_TOPICS}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)
        for topic in ROS2_SIM_TOPICS:
            client.subscribe(topic)
        self._queue_status("mosquitto", "connected")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        print(f"[backend] disconnected from MQTT broker (reason={reason_code})")
        self._queue_status("mosquitto", "disconnected")

    def _queue_status(self, source: str, event: str) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, ("__status__", {"source": source, "event": event, "ts": time.time()})
        )

    def _on_message(self, client, userdata, msg):
        if self._loop is None:
            return
        try:
            payload = json.loads(msg.payload.decode())
        except ValueError:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (msg.topic, payload))

    def _publish(self, topic: str, payload: str, retain: bool) -> None:
        self._client.publish(topic, payload, retain=retain)

    def _on_safe_state_change(self, active: bool, reasons: list[str]) -> None:
        self.safe_state.on_change(active, reasons)

    # --- lifecycle ---

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=30)
        self._client.loop_start()
        asyncio.create_task(self._consume_loop())
        asyncio.create_task(self._staleness_loop())
        asyncio.create_task(self._log_loop())

    async def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    # --- background tasks ---

    async def _consume_loop(self) -> None:
        while True:
            topic, payload = await self._queue.get()

            if topic == "__status__" or topic.startswith(LOG_TOPIC_PREFIX):
                await self._emit_raw({"type": "log", **payload})
                continue

            self._rx_count += 1
            self._last_topic = topic

            if topic == ROS2_CAMERA_TOPIC:
                # Not a scalar point: skip state_store/fault detection and
                # broadcast the frame directly, like the "log" frames above.
                await self._emit_raw(
                    {"type": "camera_frame", "format": payload.get("format"), "data": payload.get("data"), "ts": time.time()}
                )
                continue

            if topic in ROS2_SIM_TOPICS:
                for point_id, point_payload in translate(topic, payload):
                    await self._process_point(point_id, point_payload)
                continue

            await self._process_point(topic_to_point_id(topic), payload)

    async def _process_point(self, point_id: str, payload: dict) -> None:
        self.state_store.update(point_id, payload)

        value = payload.get("value")
        state = "normal"
        if isinstance(value, (int, float)):
            results = self.registry.evaluate_value(point_id, float(value), payload.get("ts", time.time()))
            new_alerts = self.alert_manager.process(results)
            if results:
                state = _worst_state(results)
            for alert in new_alerts:
                await self._emit({"type": "alert", "alert": _alert_dict(alert)})

        await self._emit({"type": "telemetry", "topic": point_id, "point_id": point_id, "payload": payload, "state": state})

    async def _staleness_loop(self) -> None:
        while True:
            for point_id in self.registry.points_with_staleness():
                seconds = self.state_store.seconds_since_seen(point_id)
                results = self.registry.evaluate_staleness(point_id, seconds)
                new_alerts = self.alert_manager.process(results)
                for result in results:
                    await self._emit(
                        {"type": "detector", "point_id": point_id, "state": result.state, "detail": result.detail}
                    )
                for alert in new_alerts:
                    await self._emit({"type": "alert", "alert": _alert_dict(alert)})
            await asyncio.sleep(STALENESS_POLL_INTERVAL)

    async def _emit(self, frame: dict) -> None:
        self._tx_count += 1
        await self._broadcast_fn(frame)

    async def _log_loop(self) -> None:
        while True:
            await asyncio.sleep(1.0)
            if self._rx_count or self._tx_count:
                print(
                    f"[backend] mqtt_rx={self._rx_count}/s -> processed -> ws_tx={self._tx_count}/s  "
                    f"last_topic={self._last_topic}"
                )
            await self._emit_raw(
                {
                    "type": "log",
                    "source": "backend",
                    "ts": time.time(),
                    "rx": self._rx_count,
                    "tx": self._tx_count,
                    "last_topic": self._last_topic,
                    "mqtt_connected": self._client.is_connected(),
                }
            )
            self._rx_count = 0
            self._tx_count = 0

    async def _emit_raw(self, frame: dict) -> None:
        """Like _emit, but doesn't count toward the ws_tx rate -- this is the
        backend reporting on itself, not telemetry it processed."""
        await self._broadcast_fn(frame)


def _worst_state(results) -> str:
    order = {"normal": 0, "warning": 1, "fault": 2}
    worst = max(results, key=lambda r: order[r.state])
    return worst.state


def _alert_dict(alert) -> dict:
    from dataclasses import asdict

    return asdict(alert)
