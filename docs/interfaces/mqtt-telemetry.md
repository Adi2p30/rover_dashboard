---
type: MQTT Topic
title: Telemetry topics
description: The sensor topics the generator publishes every tick, built by build_payloads() in publisher.py.
resource: ../../generator/publisher.py
tags: [mqtt, telemetry]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Schema

Every payload has the shape `{"ts": <unix seconds>, "value": <...>}`. `ts`
is wall-clock time at publish, not a sensor timestamp.

| Topic | `value` shape |
|-------|---------------|
| `rover/joints/{0..3}/position` | float |
| `rover/joints/{0..3}/torque` | float |
| `rover/joints/{0..3}/temperature` | float |
| `rover/wheels/{fl,fr,rl,rr}/speed` | `{ "commanded": float, "actual": float }` |
| `rover/wheels/{fl,fr,rl,rr}/slip` | float |
| `rover/battery/voltage` | float |
| `rover/battery/current` | float |
| `rover/battery/soc` | float |
| `rover/imu/orientation` | `{ "roll": float, "pitch": float, "yaw": float }` |
| `rover/imu/accel` | `{ "x": float, "y": float, "z": float }` |
| `rover/imu/gyro` | `{ "x": float, "y": float, "z": float }` |
| `rover/gps/position` | `{ "lat": float, "lon": float, "alt": float }` |
| `rover/comms/heartbeat` | float (timestamp of last heartbeat) |
| `rover/camera/heartbeat` | float (timestamp of last heartbeat) |

The backend strips the `rover/` prefix to get a **point id** (for example
`joints/0/temperature`) used throughout [the detector config](../components/backend.md)
and the [WebSocket stream](websocket-stream.md).

# Suppression

A [fault scenario](../scenarios/index.md) can suppress publication of
specific topics entirely (`Scenario.suppressed_topics`) rather than mutate
their value — this is how `sensor_dropout` and `comms_loss` surface as
[staleness](../detectors/staleness.md) on the backend instead of a bad
value.

# Related

* [Fault scenarios](../scenarios/index.md)
* [Fault detectors](../detectors/index.md)
* [Backend](../components/backend.md)
