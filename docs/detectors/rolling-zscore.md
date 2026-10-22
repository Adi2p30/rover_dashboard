---
type: Fault Detector
title: Rolling z-score
description: Rolling EWMA mean/variance z-score detector for noisy-but-bounded signals where a fixed threshold would be too rigid.
resource: ../../backend/fault_detection/zscore.py
tags: [detector, zscore]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`ZScoreDetector` maintains an exponentially-weighted mean and variance
(`alpha=0.05` by default) and flags a value whose deviation from that
rolling mean, in standard deviations, crosses `warn_z` (default `3.0`) or
`fault_z` (default `5.0`). The mean/variance update happens **after** `z`
is computed for the current value, so a single outlier can't inflate its
own variance estimate and mask itself. The first value seen for a point
just seeds the mean and reports `normal` ("warming up").

# Points using it

Configured in `backend/config.py`'s `DETECTOR_CONFIG`:

| Point | `warn_z` | `fault_z` |
|-------|----------|-----------|
| `joints/{0..3}/torque` | `3.0` | `5.0` |

# Related

No current [fault scenario](../scenarios/index.md) specifically targets
joint torque, so none is linked here as exercising this detector.
