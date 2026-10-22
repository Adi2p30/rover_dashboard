---
type: Component
title: Generator
description: Synthetic rover telemetry generator; publishes simulated sensor data over MQTT at a configurable rate with selectable fault scenarios.
resource: ../../generator/
tags: [generator, mqtt, simulation]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T18:30:41Z }
---

# Overview

A CLI process that steps a simulated rover's state forward at a fixed
timestep and publishes every telemetry point over MQTT each tick. It also
subscribes to a command topic so the active fault scenario can be switched
live, without restarting the process.

# Modules

| File | Role |
|------|------|
| [`rover_model.py`](../../generator/rover_model.py) | `RoverState` — holds the current value of every telemetry point (joints, wheels, battery, IMU, GPS, comms/camera heartbeats) and advances them one timestep at a time via `step(dt, scenario)`. |
| [`signals.py`](../../generator/signals.py) | Reusable stochastic primitives — `sine_with_noise`, `random_walk`, `ou_process` — used to synthesize realistic-looking values. |
| [`scenarios.py`](../../generator/scenarios.py) | Fault-injection scenarios; see [Fault scenarios](../scenarios/index.md). |
| [`publisher.py`](../../generator/publisher.py) | The MQTT publish loop and the `ScenarioRunner` that owns the active scenario; see [MQTT telemetry topics](../interfaces/mqtt-telemetry.md) and [MQTT control topics](../interfaces/mqtt-control.md). Also publishes a once/sec status line to `rover/log/generator` (`{"source": "generator", "rate", "scenario", "last_topic"}`), relayed by the backend into a `log` [WebSocket frame](../interfaces/websocket-stream.md) for `dashboard/logs.html`. |
| [`external_emulator.py`](../../generator/external_emulator.py) | A standalone, independently-run emulator of an external ROS 2 publisher; see [MQTT external-emulator topics](../interfaces/mqtt-external.md). |
| [`main.py`](../../generator/main.py) | CLI entry point: `python -m generator.main --scenario normal --broker-host localhost --rate 4`. |

# Related

* [Fault scenarios](../scenarios/index.md)
* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
* [Run locally](../playbooks/run-locally.md)
