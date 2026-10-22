---
type: Fault Scenario
title: joint_overheat
description: Joint 2 loses its cooling term and its temperature ramps toward a thermal fault.
resource: ../../generator/scenarios.py
tags: [scenario, thermal]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_joint_overheat` raises joint 2's temperature by `1.2 * dt` per step,
capped at `130.0`:

    j.temperature = min(j.temperature + 1.2 * dt, 130.0)

Published on `rover/joints/2/temperature`.

# Detection

Caught by the [threshold detector](../detectors/threshold.md) configured
on `joints/2/temperature` (`warn_hi=55.0`, `fault_hi=75.0`,
`hysteresis=3.0`), which should trip `warning` then `fault` as the
temperature climbs.

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
