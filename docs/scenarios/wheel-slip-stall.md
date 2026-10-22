---
type: Fault Scenario
title: wheel_slip_stall
description: The rear-left wheel stalls — actual speed collapses to zero while commanded speed stays nominal — as if stuck in regolith.
resource: ../../generator/scenarios.py
tags: [scenario, wheels]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_wheel_slip_stall` forces the rear-left wheel's actual speed to zero and
recomputes slip from the gap to commanded speed:

    w.speed_actual = 0.0
    denom = max(abs(w.speed_commanded), 1e-3)
    w.slip = abs(w.speed_commanded - w.speed_actual) / denom

Published on `rover/wheels/rl/speed` and `rover/wheels/rl/slip`.

# Detection

Caught by the [threshold detector](../detectors/threshold.md) on
`wheels/rl/slip` (`warn_hi=0.3`, `fault_hi=0.7`, `hysteresis=0.05`). Slip
approaches `1.0` once the wheel is fully stalled, well past `fault_hi`.

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
