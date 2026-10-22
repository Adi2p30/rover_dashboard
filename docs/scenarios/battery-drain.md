---
type: Fault Scenario
title: battery_drain
description: State of charge collapses roughly 20x faster than nominal, with voltage sagging proportionally to current draw.
resource: ../../generator/scenarios.py
tags: [scenario, battery]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_battery_drain` each step:

    state.battery_soc = max(0.0, state.battery_soc - 0.06 * dt)
    state.battery_current = min(state.battery_current * 1.5, 12.0)
    sag = 0.15 * state.battery_current
    state.battery_voltage = max(15.0, 25.2 * (state.battery_soc / 100.0) - sag)

Published on `rover/battery/soc`, `rover/battery/current`, and
`rover/battery/voltage`.

# Detection

Caught by the [threshold detectors](../detectors/threshold.md) on
`battery/soc` (`warn_lo=15.0`, `fault_lo=5.0`), `battery/current`
(`warn_hi=6.0`, `fault_hi=9.0`), and `battery/voltage` (`warn_lo=21.0`,
`fault_lo=19.0`).

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
