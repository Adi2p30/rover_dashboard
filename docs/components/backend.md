---
type: Component
title: Backend
description: FastAPI app that bridges MQTT into a WebSocket stream, runs per-point fault detection and alerting, and publishes a safe-state command on critical faults.
resource: ../../backend/
tags: [backend, fastapi, mqtt, fault-detection]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Overview

A single FastAPI process that subscribes to `rover/#` **and** to
[`ros2_sim`](ros2-bridge.md)'s own topic namespace (`cmd_vel`,
`joint_states`, `imu/data`, `arm_controller/controller_state`,
`camera/image_color/compressed` — `backend.config.ROS2_SIM_TOPICS`) on the
broker. `ros2_sim.fake_robot` is this project's only live telemetry
source today, so the backend is not independent of it in practice, even
though the two started out, and remain, separately testable: everything
under `rover/#` is still a legitimate input if something publishes there.
[`ros2_translate.py`](../../backend/ros2_translate.py) maps the ROS 2
message shapes coming off `ros2_sim`'s topics onto this project's
`rover/*` point schema before anything else (`state_store`, fault
detection, the WebSocket broadcast) sees them — those never see a ROS 2
message shape. The backend updates in-memory state per telemetry point,
runs every configured fault detector against incoming values, feeds
detector results through the alert manager, and fans the result out to
every connected WebSocket client. It also exposes REST endpoints for
polling state and alerts.

# Modules

| File | Role |
|------|------|
| [`app.py`](../../backend/app.py) | FastAPI app: REST endpoints and the `/ws` WebSocket endpoint; see [HTTP API](../interfaces/http-api.md) and [WebSocket stream](../interfaces/websocket-stream.md). |
| [`mqtt_bridge.py`](../../backend/mqtt_bridge.py) | `MQTTBridge` — bridges paho-mqtt's network thread into asyncio via a queue, drains it to update state, run detection, and broadcast frames. Topics in `ROS2_SIM_TOPICS` are routed through `ros2_translate.translate()` first; `ROS2_CAMERA_TOPIC` is special-cased even earlier and broadcast directly as a `camera_frame` WebSocket frame, bypassing `state_store`/fault detection entirely (an image isn't a scalar point, and `state_store`'s bounded history isn't meant to hold `HISTORY_MAXLEN` frames of image bytes per point). Also relays anything under `rover/log/` plus its own connect/disconnect and per-second rx/tx stats as `log` [WebSocket frames](../interfaces/websocket-stream.md), via `_emit_raw` so self-reporting never inflates the `ws_tx` rate it reports on itself. |
| [`ros2_translate.py`](../../backend/ros2_translate.py) | `translate(topic, payload)` — turns one `ros2_sim` ROS 2-shaped MQTT message into zero or more `rover/*` point payloads. Looks up `/joint_states` joints **by name** (`ROS2_WHEEL_JOINT_NAMES`/`ROS2_ARM_JOINT_NAMES` in `config.py`), since that one message carries both wheel and arm joints and the two subsystems' names can arrive in any order. |
| [`state_store.py`](../../backend/state_store.py) | `StateStore` — in-memory latest-value store plus bounded history per telemetry point (`HISTORY_MAXLEN = 300`). |
| [`config.py`](../../backend/config.py) | Broker address, ports, `ROS2_SIM_TOPICS`/`ROS2_CAMERA_TOPIC`/`ROS2_WHEEL_JOINT_NAMES`/`ROS2_ARM_JOINT_NAMES` (see [ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md)), `DETECTOR_CONFIG` — the per-point detector assignment (see [Fault detectors](../detectors/index.md)) — and `LOG_TOPIC_PREFIX` (`rover/log/`), the namespace `mqtt_bridge.py` treats as pipeline status rather than a telemetry point. |
| `fault_detection/` | Detector implementations and the registry that builds them from `DETECTOR_CONFIG`; see [Fault detectors](../detectors/index.md). |
| `alerting/` | Severity mapping, active-alert bookkeeping, and the safe-state publisher; see [Alerting](../alerting/index.md). |

# Related

* [ROS 2 bridge (simulated)](ros2-bridge.md)
* [ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md)
* [Fault detectors](../detectors/index.md)
* [Alerting](../alerting/index.md)
* [HTTP API](../interfaces/http-api.md)
* [WebSocket stream](../interfaces/websocket-stream.md)
