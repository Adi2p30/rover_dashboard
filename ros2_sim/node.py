"""A fake rclpy-shaped Node: create_publisher / create_subscription / spin,
backed by this repo's Mosquitto broker instead of real DDS.

Deliberately lives outside the "rover/#" MQTT tree the generator/backend
use -- these are meant to be exactly the topic names a real ROS 2 bridge
would use (/cmd_vel, /odom, /imu/data, ...), not this project's internal
telemetry schema, so the existing backend never sees or touches them.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Callable

import paho.mqtt.client as mqtt

from ros2_sim.msgs import from_dict

DEFAULT_BROKER_HOST = "localhost"
DEFAULT_BROKER_PORT = 1883


def _to_mqtt_topic(ros2_topic: str) -> str:
    """MQTT topics can't usefully start with '/' (it creates an empty first
    level), so strip it -- '/imu/data' -> 'imu/data'."""
    return ros2_topic.lstrip("/")


class Publisher:
    def __init__(self, client: mqtt.Client, ros2_topic: str, msg_type: type):
        self._client = client
        self.topic = ros2_topic
        self.msg_type = msg_type
        self._mqtt_topic = _to_mqtt_topic(ros2_topic)

    def publish(self, msg) -> None:
        if not isinstance(msg, self.msg_type):
            raise TypeError(f"{self.topic}: expected {self.msg_type.__name__}, got {type(msg).__name__}")
        self._client.publish(self._mqtt_topic, json.dumps(asdict(msg)), qos=0)


class Subscription:
    def __init__(self, ros2_topic: str, msg_type: type):
        self.topic = ros2_topic
        self.msg_type = msg_type


class Node:
    """Stands in for rclpy.node.Node. Create one per fake "ROS 2 process",
    wire up publishers/subscriptions, then spin()."""

    def __init__(self, name: str, broker_host: str = DEFAULT_BROKER_HOST, broker_port: int = DEFAULT_BROKER_PORT):
        self.name = name
        self._subs: dict[str, tuple[type, Callable]] = {}
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ros2sim-{name}")
        self._client.on_message = self._on_message
        self._client.connect(broker_host, broker_port, keepalive=30)
        self._client.loop_start()

    def create_publisher(self, msg_type: type, topic: str, qos_depth: int = 10) -> Publisher:
        return Publisher(self._client, topic, msg_type)

    def create_subscription(self, msg_type: type, topic: str, callback: Callable, qos_depth: int = 10) -> Subscription:
        mqtt_topic = _to_mqtt_topic(topic)
        self._subs[mqtt_topic] = (msg_type, callback)
        self._client.subscribe(mqtt_topic)
        return Subscription(topic, msg_type)

    def publish_status(self, topic: str, payload: dict) -> None:
        """Publishes arbitrary status JSON on a literal MQTT topic (no ROS 2
        message type, no leading-slash stripping) -- for the rover/log/
        heartbeat, which deliberately lives in the project's shared log
        namespace rather than this node's own ROS 2 topic tree."""
        self._client.publish(topic, json.dumps(payload), qos=0)

    def _on_message(self, client, userdata, msg) -> None:
        entry = self._subs.get(msg.topic)
        if entry is None:
            return
        msg_type, callback = entry
        try:
            data = json.loads(msg.payload.decode())
            obj = from_dict(msg_type, data)
        except (ValueError, TypeError) as exc:
            print(f"[ros2sim:{self.name}] bad message on /{msg.topic}: {exc}")
            return
        callback(obj)

    def spin(self) -> None:
        """Blocks, dispatching subscription callbacks as messages arrive
        (the network I/O itself runs on paho's background thread)."""
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

    def destroy_node(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
