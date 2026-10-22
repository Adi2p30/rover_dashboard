---
type: API Endpoint
title: WebSocket stream
description: The /ws endpoint the dashboard connects to for live telemetry, detector, and alert frames.
resource: ../../backend/app.py
tags: [api, websocket]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Protocol

On connect, the server immediately sends a snapshot frame, then one frame
per subsequent event. The client never needs to send anything beyond the
initial handshake.

| `type` | Shape | Sent |
|--------|-------|------|
| `snapshot` | `{"type": "snapshot", "state": <StateStore.snapshot()>, "alerts": <AlertManager.snapshot()>}` | Once, immediately on connect. |
| `telemetry` | `{"type": "telemetry", "topic": str, "point_id": str, "payload": {...}, "state": "normal"\|"warning"\|"fault"}` | On every MQTT message received on `rover/#` (the backend's subscription), including [external-emulator](mqtt-external.md) and dict-valued topics. `state` only reflects a detector result when `payload.value` is numeric; otherwise it stays `"normal"`. |
| `detector` | `{"type": "detector", "point_id": str, "state": str, "detail": str}` | Once per second per staleness-monitored point, from the staleness poll loop. |
| `alert` | `{"type": "alert", "alert": <Alert dict>}` | Whenever a new alert is raised (severity changed) by the [alert manager](../alerting/alert-manager.md). |
| `log` | See below | Once per second each from the generator and the backend, plus once on an actual MQTT connect/disconnect. Drives [`dashboard/logs.html`](../../dashboard/logs.html). |
| `camera_frame` | `{"type": "camera_frame", "format": "png", "data": str, "ts": float}` | On every `ros2_sim` MQTT message on `backend.config.ROS2_CAMERA_TOPIC` (`camera/image_color/compressed`). `data` is the base64 PNG as published by `ros2_sim.fake_robot` (see [ROS 2 bridge topics](ros2-bridge-topics.md)); the dashboard sets it directly as an `<img>`'s `src` (`data:image/png;base64,...`). |

`state` on a `telemetry` frame is the worst detector state across all
detectors attached to that point id, via `backend.mqtt_bridge._worst_state`.

`camera_frame` bypasses `state_store` and fault detection entirely --
`backend.mqtt_bridge` special-cases `ROS2_CAMERA_TOPIC` before the generic
`ROS2_SIM_TOPICS`/`translate()` path and broadcasts it straight through
with `_emit_raw`, the same way `log` frames are. An image isn't a scalar
point, and `state_store`'s bounded history (`HISTORY_MAXLEN`) is sized for
numeric values, not `HISTORY_MAXLEN` frames of image bytes per client
snapshot.

## `log` frame shapes

`log` frames never go through fault detection or `state_store` — they're
pipeline self-reporting, not telemetry. `backend.mqtt_bridge.MQTTBridge`
relays them with `_emit_raw` (doesn't count toward the `ws_tx` rate it
reports on itself) and distinguishes them by `source`:

| `source` | Shape | Origin |
|----------|-------|--------|
| `generator` | `{"type": "log", "source": "generator", "ts": float, "rate": int, "scenario": str, "last_topic": str}` | The generator publishes this once/sec to MQTT topic `rover/log/generator` ([`generator/publisher.py`](../../generator/publisher.py)); the backend relays anything under the [`LOG_TOPIC_PREFIX`](../../backend/config.py) `rover/log/` straight through instead of treating it as a telemetry point. |
| `backend` | `{"type": "log", "source": "backend", "ts": float, "rx": int, "tx": int, "last_topic": str, "mqtt_connected": bool}` | The backend's own `_log_loop`, once/sec — `rx`/`tx` are the same counters behind its `mqtt_rx=.../s -> processed -> ws_tx=.../s` terminal line. `mqtt_connected` is the live broker-connection state, polled every second rather than only at connect time, since a browser opening `logs.html` after the one-off connect event would otherwise never see it. |
| `mosquitto` | `{"type": "log", "source": "mosquitto", "event": "connected"\|"disconnected", "ts": float}` | Queued by the backend's paho `on_connect`/`on_disconnect` callbacks via `_queue_status`. Fires once per actual transition — `logs.html` uses the periodic `backend` frame's `mqtt_connected` field as the primary signal and this only for the human-readable "backend connected to broker" tail line. |

# Related

* [Dashboard](../components/dashboard.md)
* [Fault detectors](../detectors/index.md)
* [Alert manager](../alerting/alert-manager.md)
