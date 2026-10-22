---
type: Component
title: Safe-state publisher
description: Publishes the retained rover/command/safe_state MQTT message whenever the active-CRITICAL-alert count transitions to or from zero.
resource: ../../backend/alerting/safe_state.py
tags: [alerting, safe-state]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`SafeStatePublisher.on_change(active, reasons)` is called by the
[alert manager](alert-manager.md) only on a transition (not on every
tick) and publishes a retained message:

    {"active": <bool>, "reasons": [<point_id>, ...], "ts": <float>}

on `rover/command/safe_state`. `reasons` is the list of point ids
currently in `CRITICAL`.

# Related

* [MQTT control topics](../interfaces/mqtt-control.md)
* [Alert manager](alert-manager.md)
