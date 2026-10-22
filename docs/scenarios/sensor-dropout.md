---
type: Fault Scenario
title: sensor_dropout
description: The IMU orientation topic stops publishing entirely, surfacing as staleness on the backend rather than a bad value.
resource: ../../generator/scenarios.py
tags: [scenario, sensor]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Behavior

`_sensor_dropout`'s `apply_fn` is a no-op; the fault is entirely expressed
through `suppressed_topics = {"rover/imu/orientation"}`, which makes
`Scenario.should_publish()` return `False` for that topic so the publish
loop skips it.

# Detection

Caught by the [staleness detector](../detectors/staleness.md) on
`imu/orientation` (`warn_timeout=3.0`, `fault_timeout=8.0`), which is
polled against elapsed time rather than driven by message values — exactly
what catches a topic that stops arriving.

# Related

* [MQTT telemetry topics](../interfaces/mqtt-telemetry.md)
