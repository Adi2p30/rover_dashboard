---
type: Fault Detector
title: Rate of change
description: Flags sudden |delta value| / delta t jumps that exceed a configured rate — useful for catching sensor glitches or unrealistic step changes.
resource: ../../backend/fault_detection/rate_of_change.py
tags: [detector, rate-of-change]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`RateOfChangeDetector` tracks the previous value and timestamp for a
point and computes `|value - prev_value| / max(ts - prev_ts, 1e-3)` on
every update, comparing it against `warn_rate` and `fault_rate`. The
first value seen just seeds the previous value/timestamp and reports
`normal` ("warming up").

# Points using it

Configured in `backend/config.py`'s `DETECTOR_CONFIG`:

| Point | `warn_rate` | `fault_rate` |
|-------|-------------|--------------|
| `joints/{0..3}/position` | `2.0` | `4.0` |

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
