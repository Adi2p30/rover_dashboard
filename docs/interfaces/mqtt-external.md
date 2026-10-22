---
type: MQTT Topic
title: External-emulator topics
description: Topics from a standalone emulator of an external ROS 2 publisher (Leo Rover base stack), bridged onto the same MQTT bus for a fixed-duration burst.
resource: ../../generator/external_emulator.py
tags: [mqtt, ros2, emulator]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Overview

Run independently of `generator.main` via
`python -m generator.external_emulator --rate 50 --duration 120`. It
emulates four ROS 2 topics with a simple unicycle/skid-steer model, so this
project's MQTT pipeline can be exercised without a real ROS 2 install.

The backend subscribes to `rover/#`, so these topics flow through the same
[WebSocket stream](websocket-stream.md) as everything else, and the
dashboard renders them in a dedicated "External ROS 2 Feed" panel
(`dashboard/js/charts.js`'s `ext/*` charts and `handleTelemetry`'s
`external/*` branches). The one thing nothing downstream depends on is
the `--ros2-fields` payload shape (see below) — the dashboard only
understands the default flattened schema.

# Topics

| Topic | Emulates (ROS 2) |
|-------|------------------|
| `rover/external/cmd_vel` | `/cmd_vel` (`geometry_msgs/msg/Twist`) |
| `rover/external/odom` | `/merged_odom` (`nav_msgs/msg/Odometry`) |
| `rover/external/imu` | `/imu/data` (`sensor_msgs/msg/Imu`) |
| `rover/external/joint_states` | `/joint_states` (`sensor_msgs/msg/JointState`) |

Every payload wraps the topic's `value` with `{"ts", "seq", "rate_hz",
"elapsed", "remaining", "value": {...}}`.

# Payload shape

By default `value` uses a flattened schema (plain `roll/pitch/yaw`,
`x/y` position, and so on). Passing `--ros2-fields` instead shapes
`odom`/`imu`/`joint_states` closer to the real ROS 2 messages: a
`header.stamp.sec/nanosec` + `frame_id`, quaternion orientation via
`_rpy_to_quaternion`, and illustrative (not measured) diagonal covariance
matrices. This is opt-in since nothing downstream currently depends on it.

# Related

* [Generator](../components/generator.md)
