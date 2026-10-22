---
type: Fault Scenario
title: comms_loss
description: The comms heartbeat topic stops publishing entirely, surfacing as staleness on the backend.
resource: ../../generator/scenarios.py
tags: [scenario, comms]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_comms_loss`'s `apply_fn` is a no-op; the fault is expressed through
`suppressed_topics = {"rover/comms/heartbeat"}`.

This is also the scenario this project's architecture is specifically
designed to keep working through — see
[the platform comparison](../decisions/platform-comparison.md), which
treats comms blackout as a first-class requirement favoring a self-hosted,
MQTT-native stack over a cloud-dependent one.

# Detection

Caught by the [staleness detector](../detectors/staleness.md) on
`comms/heartbeat` (`warn_timeout=3.0`, `fault_timeout=8.0`). A sustained
`comms_loss` drives the active-`CRITICAL`-alert count above zero, which
trips [safe-state](../alerting/safe-state.md).

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
* [Platform comparison](../decisions/platform-comparison.md)
