---
type: Fault Detector
title: Staleness
description: Heartbeat/staleness detector polled against seconds-since-last-message rather than driven by new values — catches a topic that stops publishing entirely.
resource: ../../backend/fault_detection/staleness.py
tags: [detector, staleness, heartbeat]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

Unlike the other detectors, `StalenessDetector` isn't driven by incoming
messages. `MQTTBridge._staleness_loop` polls every
`STALENESS_POLL_INTERVAL` (1.0s) for each point configured with a
staleness detector, asking `StateStore.seconds_since_seen(point_id)` and
comparing it against `warn_timeout`/`fault_timeout`. A point never seen at
all reports `fault` ("never seen").

# Points using it

Configured in `backend/config.py`'s `DETECTOR_CONFIG`:

| Point | `warn_timeout` | `fault_timeout` |
|-------|-----------------|-----------------|
| `comms/heartbeat` | `3.0`s | `8.0`s |
| `camera/heartbeat` | `3.0`s | `8.0`s |
| `imu/orientation` | `3.0`s | `8.0`s |

# Related

* [comms_loss](../scenarios/comms-loss.md)
* [sensor_dropout](../scenarios/sensor-dropout.md)
