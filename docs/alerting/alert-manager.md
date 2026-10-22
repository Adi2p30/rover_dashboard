---
type: Component
title: Alert manager
description: Tracks active alerts per point and an append-only alert log; triggers the safe-state publisher whenever the count of active CRITICAL alerts changes.
resource: ../../backend/alerting/alert_manager.py
tags: [alerting]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Severity mapping

[`rules.py`](../../backend/alerting/rules.py) maps a detector's `state` to
an `Alert` severity:

| Detector state | Severity |
|-----------------|----------|
| `normal` | none (no alert) |
| `warning` | `WARNING` |
| `fault` | `CRITICAL` |

# Behavior

`AlertManager.process()` takes a batch of `DetectorResult`s per tick:

* A result mapping to no alert clears any existing active alert for that point.
* A result whose severity differs from the currently active alert for that
  point replaces it, appends to the bounded `alert_log` (`ALERT_LOG_MAXLEN
  = 200`), and is returned as newly emitted (for WebSocket broadcast).
* A result at the same severity as the current alert just refreshes the
  detail text without re-logging (dedupe).

After processing, it recomputes whether any point is `CRITICAL` and calls
`on_safe_state_change` only on a transition — see
[Safe-state publisher](safe-state.md).

# Related

* [Fault detectors](../detectors/index.md)
* [Safe-state publisher](safe-state.md)
* [WebSocket stream](../interfaces/websocket-stream.md)
