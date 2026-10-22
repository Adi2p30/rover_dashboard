---
type: Component
title: ROS 2 bridge (simulated)
description: A fake rclpy-shaped pub/sub interface (Node/create_publisher/create_subscription) backed by this project's Mosquitto broker, publishing the Leo Rover 1.9 / Arducam IMX477 / WidowX AI reference topic set with dataclasses shaped like real ROS 2 messages.
resource: ../../ros2_sim/
tags: [ros2, mqtt, simulation]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Overview

`ros2_sim/` is a separately testable module from the rest of this project
— the dashboard never imports it, and the generator package (`generator/`)
has shrunk to just `signals.py`, reused here for stochastic motion. It is
**not**, however, independent in practice: `ros2_sim.fake_robot` is this
project's only live telemetry source today, and `backend/ros2_translate.py`
subscribes to several of its topics directly (see
[Backend](backend.md) and [ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md)).
It exists to give subscriber code a real interface to write against —
`node.create_subscription(Imu, "/imu/data", callback)` — before a real ROS
2 install or rover is available. There is no `rclpy` and no DDS anywhere
in it; `ros2_sim.node.Node` just mimics rclpy's shape over plain MQTT, and
`ros2_sim.msgs` has dataclasses matching real ROS 2 message fields closely
enough that swapping the transport out for a real
`rclpy.create_subscription` later wouldn't change subscriber code.

It lives on its own MQTT topic namespace — literal ROS 2 topic names
(`/cmd_vel`, `/imu/data`, ...) with the leading `/` stripped for MQTT
(`cmd_vel`, `imu/data`) — rather than this project's `rover/#` tree. The
backend's generic `rover/#` subscription doesn't pick these up on its own;
it subscribes to the specific `ros2_sim` topics it needs explicitly
(`backend.config.ROS2_SIM_TOPICS`), separately from `rover/#`.

The topic set matches a specific reference hardware stack: a Leo Rover 1.9
base, an Arducam IMX477 HQ camera, and a WidowX AI arm. Earlier versions of
this bridge also published `/odom`, `/battery`, and `/diagnostics` — those
aren't in that reference topic list and have been removed (see
[ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md) for what
replaced the load-bearing one, `/battery`, on the dashboard).

# Modules

| File | Role |
|------|------|
| [`msgs.py`](../../ros2_sim/msgs.py) | Dataclasses matching `geometry_msgs`/`nav_msgs`/`sensor_msgs`/`trajectory_msgs`/`control_msgs`/`tf2_msgs` field-for-field: `Twist`, `Odometry` (+ `PoseWithCovariance`/`TwistWithCovariance`), `JointState`, `Imu`, `Image`/`CameraInfo`/`CompressedImage` (+ `RegionOfInterest`), `JointTrajectory`/`JointTrajectoryControllerState` (+ `JointTrajectoryPoint`/`Duration`), `TFMessage` (+ `TransformStamped`/`Transform`). `Image`/`CompressedImage.data` are base64 strings (JSON has no byte-array type). `from_dict(cls, data)` is the generic recursive reconstructor used on the subscriber side (the inverse of `dataclasses.asdict`). |
| [`png_encode.py`](../../ros2_sim/png_encode.py) | A minimal stdlib-only (`zlib`+`struct`) PNG encoder — no Pillow/OpenCV dependency. Used to give `/camera/*/compressed` topics a real, browser-decodable image instead of a placeholder byte blob. |
| [`node.py`](../../ros2_sim/node.py) | `Node`, `Publisher`, `Subscription` — the fake rclpy surface. `Node(name)` connects to the broker; `create_publisher(msg_type, topic)` / `create_subscription(msg_type, topic, callback)` / `spin()` / `destroy_node()` mirror rclpy's `Node` API. |
| [`fake_robot.py`](../../ros2_sim/fake_robot.py) | The producer side: `RoverSim` (unicycle/skid-steer base, reusing [`generator/signals.py`](../../generator/signals.py)), `ArmSim` (6-joint WidowX AI, sine-wave commanded trajectory + first-order actuator lag so `desired != actual`), and `CameraSim` (synthetic low-res noise frames). Drives all topics; camera topics publish at a slower, independent rate (every `CAMERA_TICK_DIVISOR` ticks). `python -m ros2_sim.fake_robot --rate 10`. |
| [`echo.py`](../../ros2_sim/echo.py) | Example/reference subscriber: `node.create_subscription(...)` per topic, printing each typed message like `ros2 topic echo`. `python -m ros2_sim.echo [topics...]`. |

# Related

* [ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md)
* [Backend](backend.md) — subscribes to several of these topics directly; not independent of this bridge in practice.
* [Broker](broker.md)
* [MQTT external-emulator topics](../interfaces/mqtt-external.md) — a different, older, flat-schema ROS 2 emulation inside the `rover/#` tree; not the same thing as this bridge.
