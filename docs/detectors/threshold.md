---
type: Fault Detector
title: Threshold (with hysteresis)
description: Fixed warn/fault bounds with a hysteresis band that must be cleared before severity drops, avoiding chatter at the boundary.
resource: ../../backend/fault_detection/threshold.py
tags: [detector, threshold]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`ThresholdDetector` is configured with any of `warn_lo`, `warn_hi`,
`fault_lo`, `fault_hi`, and a `hysteresis` margin. Once a severity is
raised, the value must clear the corresponding threshold by `hysteresis`
before severity drops back down, so a value oscillating right at a
boundary doesn't flap between states every tick.

# Points using it

Configured in `backend/config.py`'s `DETECTOR_CONFIG`:

| Point | `warn` | `fault` | `hysteresis` |
|-------|--------|---------|--------------|
| `joints/{0..3}/temperature` | `hi=55.0` | `hi=75.0` | `3.0` |
| `battery/voltage` | `lo=21.0` | `lo=19.0` | `0.3` |
| `battery/current` | `hi=6.0` | `hi=9.0` | `0.5` |
| `battery/soc` | `lo=15.0` | `lo=5.0` | `2.0` |
| `wheels/{fl,fr,rl,rr}/slip` | `hi=0.3` | `hi=0.7` | `0.05` |

# Related

* [joint_overheat](../scenarios/joint-overheat.md)
* [battery_drain](../scenarios/battery-drain.md)
* [wheel_slip_stall](../scenarios/wheel-slip-stall.md)
