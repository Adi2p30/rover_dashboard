---
type: Component
title: Broker
description: Local Mosquitto MQTT broker started via docker-compose; the transport every other component connects to.
resource: ../../docker-compose.yml
tags: [mqtt, broker, infra]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Overview

`docker-compose up -d` starts a single `eclipse-mosquitto:2` container,
exposing port `1883` on localhost and mounting
[`mosquitto/config/`](../../mosquitto/config) for configuration.

# Configuration

[`mosquitto.conf`](../../mosquitto/config/mosquitto.conf):

* `listener 1883`
* `allow_anonymous true` — no auth; fine for a local dev broker, not for anything exposed beyond localhost.
* `persistence false` — no retained-message persistence to disk across restarts (retained messages such as `rover/status/scenario` and `rover/command/safe_state` only survive while the broker process is up).
* `log_dest stdout`

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
* [MQTT control topics](../interfaces/mqtt-control.md)
* [Run locally](../playbooks/run-locally.md)
