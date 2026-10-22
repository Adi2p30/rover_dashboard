---
type: MQTT Topic
title: Control and status topics
description: Topics used to switch the generator's active fault scenario and to announce safe-state transitions.
resource: ../../generator/publisher.py
tags: [mqtt, control]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Topics

| Topic | Direction | Retained | Payload |
|-------|-----------|----------|---------|
| `rover/command/set_scenario` | backend/operator -> generator | no | `{"name": "<scenario>"}` |
| `rover/status/scenario` | generator -> subscribers | yes | `{"name": "<scenario>"}`, published on connect and on every successful switch |
| `rover/command/safe_state` | backend -> subscribers | yes | `{"active": bool, "reasons": [<point_id>, ...], "ts": float}` |

`rover/command/safe_state` is published by
[`SafeStatePublisher`](../alerting/safe-state.md) whenever the set of
active `CRITICAL` alerts transitions to or from empty; `reasons` lists the
point ids currently in `CRITICAL`.

Switching scenarios through the dashboard or the REST API
(`POST /api/scenario`) does not publish `set_scenario` directly — the
backend's `MQTTBridge.set_scenario()` does, so the generator and backend
agree on the current scenario through the broker rather than through a
direct call.

# Related

* [Switch scenario](../playbooks/switch-scenario.md)
* [Safe-state publisher](../alerting/safe-state.md)
* [HTTP API](http-api.md)
