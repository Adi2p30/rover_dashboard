---
type: Playbook
title: Switch scenario
description: Change the generator's active fault-injection scenario at runtime, from the dashboard dropdown or the REST API.
tags: [playbook, scenario]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Steps

From the dashboard, use the scenario dropdown — it calls `setScenario()`
in [`ws_client.js`](../../dashboard/js/ws_client.js), which POSTs to the
backend.

From the command line:

```bash
curl -X POST localhost:8000/api/scenario -H 'Content-Type: application/json' -d '{"name":"joint_overheat"}'
```

`name` must be one of the keys in `generator.scenarios.SCENARIOS` — see
[Fault scenarios](../scenarios/index.md).

# What happens

1. The backend's `POST /api/scenario` handler calls `MQTTBridge.set_scenario()`.
2. That publishes `rover/command/set_scenario` with `{"name": ...}`.
3. The generator's `ScenarioRunner` picks it up and switches, then
   re-publishes the retained `rover/status/scenario`.

See [MQTT control topics](../interfaces/mqtt-control.md) for the full
topic protocol.

# Related

* [HTTP API](../interfaces/http-api.md)
* [MQTT control topics](../interfaces/mqtt-control.md)
* [Fault scenarios](../scenarios/index.md)
