---
type: Fault Scenario
title: normal
description: Baseline operation — no injected fault; every topic publishes nominal, lightly-noised signals.
resource: ../../generator/scenarios.py
tags: [scenario, baseline]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_normal` is a no-op `apply_fn`; `RoverState.step()` runs unmodified. This
is `DEFAULT_SCENARIO` and the generator's `--scenario` default.

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
