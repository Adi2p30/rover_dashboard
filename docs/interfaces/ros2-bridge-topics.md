---
type: MQTT Topic
title: ROS 2 bridge topics
description: The topics ros2_sim.fake_robot publishes, matching the Leo Rover 1.9 / Arducam IMX477 / WidowX AI reference topic list, and the exact JSON shape of each message.
resource: ../../ros2_sim/
tags: [mqtt, ros2, simulation]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Overview

Every message is a `dataclasses.asdict()` of the corresponding type in
[`ros2_sim/msgs.py`](../../ros2_sim/msgs.py), published with `qos=0` to the
MQTT topic (ROS 2 topic name with the leading `/` stripped). The wire
format is plain JSON — no ROS 2 serialization, no CDR — chosen so
`ros2_sim.msgs.from_dict` can reconstruct the exact nested dataclass on
the subscriber side. Byte-array fields (`Image`/`CompressedImage.data`)
are base64 strings, matching the convention rosbridge_suite/roslibjs
already use for a ROS 2 byte array on the wire as JSON. All samples below
were captured live from `ros2_sim.fake_robot` over the real broker.

This topic set matches a specific reference hardware stack: a **Leo Rover
1.9** base, an **Arducam IMX477 HQ Camera**, and a **WidowX AI** arm. The
`Direction` column is from that platform's own point of view, as a real
ROS 2 graph would see it — not from `fake_robot.py`'s point of view, which
only ever publishes (see **Self-published "Subscribe" topics** below).

Earlier versions of this bridge also published `/odom`, `/battery`, and
`/diagnostics`. None of those are in this reference topic list, and all
three have been removed. `/battery` was load-bearing for the live
dashboard (it was the only source for the Battery panel and
`battery/*` fault detectors in `backend/config.py`) — removing it also
removed that panel and those detectors; see
[Backend](../components/backend.md) and
[Dashboard](../components/dashboard.md).

## Self-published "Subscribe" topics

On the real platform, `/cmd_vel`, `/heading_controller/cmd_vel`, and
`/arm_controller/joint_trajectory` are inputs: something upstream (teleop,
a nav stack, a motion planner) publishes to them, and the rover/arm
subscribes. This simulator has no such upstream node, so — the same way it
already did for `/cmd_vel` before this topic list existed —
`ros2_sim.fake_robot` self-publishes synthetic commands on all three, so
`ros2_sim.echo` (or anything else) has something to observe there. A real
bridge replacing `fake_robot.py` would instead have something else
publishing these and the rover/arm subscribing.

# Topics

## Movement (Leo Rover 1.9)

| MQTT topic | ROS 2 topic | Message type | Direction |
|------------|-------------|---------------|-----------|
| `cmd_vel` | `/cmd_vel` | `Twist` (`geometry_msgs/msg/Twist`) | Subscribe (self-published here — see above) |
| `heading_controller/cmd_vel` | `/heading_controller/cmd_vel` | `Twist` | Subscribe (self-published here — see above) |
| `merged_odom` | `/merged_odom` | `Odometry` (`nav_msgs/msg/Odometry`) | Publish |
| `wheel_odom` | `/wheel_odom` | `Odometry` | Publish |
| `imu/data` | `/imu/data` | `Imu` (`sensor_msgs/msg/Imu`) | Publish |
| `joint_states` | `/joint_states` | `JointState` (`sensor_msgs/msg/JointState`) | Publish (wheel **and** arm joints — see below) |
| `tf` | `/tf` | `TFMessage` (`tf2_msgs/msg/TFMessage`) | Publish |
| `tf_static` | `/tf_static` | `TFMessage` | Publish (once at startup) |

## Camera (Arducam IMX477 HQ Camera)

| MQTT topic | ROS 2 topic | Message type | Direction |
|------------|-------------|---------------|-----------|
| `camera/image_raw` | `/camera/image_raw` | `Image` (`sensor_msgs/msg/Image`) | Publish |
| `camera/camera_info` | `/camera/camera_info` | `CameraInfo` (`sensor_msgs/msg/CameraInfo`) | Publish |
| `camera/image_color` | `/camera/image_color` | `Image` | Publish |
| `camera/image_color/compressed` | `/camera/image_color/compressed` | `CompressedImage` (`sensor_msgs/msg/CompressedImage`) | Publish |
| `camera/image_mono` | `/camera/image_mono` | `Image` | Publish |
| `camera/image_rect` | `/camera/image_rect` | `Image` | Publish |
| `camera/image_rect_color` | `/camera/image_rect_color` | `Image` | Publish |
| `camera/image_rect_color/compressed` | `/camera/image_rect_color/compressed` | `CompressedImage` | Publish |

Frames are a synthetic 64x48 placeholder resolution (`CAMERA_WIDTH`/
`CAMERA_HEIGHT` in `fake_robot.py`), not the IMX477's real resolution —
random noise, not an actual picture. They publish at a slower, independent
rate (every `CAMERA_TICK_DIVISOR` = 5 ticks) than the other topics, since
image payloads are much larger. `*_rect*` topics are raw frames here, not
actually lens-corrected — there's no real lens to correct for.

`camera/image_color/compressed` is the one camera topic the backend
subscribes to and broadcasts live to the dashboard (as a `camera_frame`
WebSocket frame) — see [WebSocket stream](websocket-stream.md). The other
7 camera topics exist on the bus (and `ros2_sim.echo` can subscribe to
any of them) but aren't wired into the backend/dashboard.

## Arm (WidowX AI)

| MQTT topic | ROS 2 topic | Message type | Direction |
|------------|-------------|---------------|-----------|
| `joint_states` | `/joint_states` | `JointState` | Publish (same combined message as Movement, above) |
| `arm_controller/joint_trajectory` | `/arm_controller/joint_trajectory` | `JointTrajectory` (`trajectory_msgs/msg/JointTrajectory`) | Subscribe (self-published here — see above) |
| `arm_controller/controller_state` | `/arm_controller/controller_state` | `JointTrajectoryControllerState` (`control_msgs/msg/JointTrajectoryControllerState`) | Publish |
| `tf` | `/tf` | `TFMessage` | Publish (same combined message as Movement, above — carries an additional `arm_base_link -> gripper_link` transform) |
| `tf_static` | `/tf_static` | `TFMessage` | Publish (same combined message as Movement, above — carries an additional `base_link -> arm_base_link` transform) |

The arm is 6 joints: `waist`, `shoulder`, `elbow`, `wrist_angle`,
`wrist_rotate`, `gripper`. Each chases a sine-wave commanded trajectory
with a first-order actuator lag (`ArmSim` in `fake_robot.py`), so
`desired != actual` and `/arm_controller/controller_state.error` is
non-zero and settling, not a constant.

`/tf`'s `arm_base_link -> gripper_link` transform is a **simplified,
position-only** 3-joint (waist/shoulder/elbow) planar approximation, not
real forward kinematics — `wrist_angle`, `wrist_rotate`, and `gripper`
don't move it, only the (unmodeled) end-effector orientation/grip would.

`JointTrajectoryControllerState` here only has `desired`/`actual`/`error`
— the real message (`control_msgs`, Humble+) also has `reference`/
`feedback`/`output` (newer aliases added for API continuity) and
`multi_dof_*` fields for Cartesian control, neither of which this
single-arm, joint-space simulation produces.

# Message formats

### `/cmd_vel`, `/heading_controller/cmd_vel` — `Twist`

```json
{
  "linear": {"x": 0.38841958863353354, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.04691449195988463}
}
```

### `/merged_odom`, `/wheel_odom` — `Odometry`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": "odom"},
  "child_frame_id": "base_footprint",
  "pose": {
    "pose": {
      "position": {"x": 0.1488450843434255, "y": 0.0005961686414966519, "z": 0.0},
      "orientation": {"x": 0.0, "y": 0.0, "z": 0.0066927313833479675, "w": 0.9999776034225119}
    },
    "covariance": [0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01, 0.0, "... 36 values total"]
  },
  "twist": {
    "twist": {
      "linear": {"x": 0.38841958863353354, "y": 0.0, "z": 0.0},
      "angular": {"x": 0.0, "y": 0.0, "z": 0.04691449195988463}
    },
    "covariance": [0.001, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001, 0.0, "... 36 values total"]
  }
}
```

### `/joint_states` — `JointState` (wheels + arm, combined)

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": ""},
  "name": ["wheel_FL_joint", "wheel_FR_joint", "wheel_RL_joint", "wheel_RR_joint",
           "waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"],
  "position": [1.9542871212840072, 2.014968338844235, 1.9542871212840072, 2.014968338844235,
               0.05004044239473364, 0.03456629017768277, 0.0597225361728409, 0.05574208053272374,
               0.12268742751697531, 0.05370687122227748],
  "velocity": [5.072588333338042, 5.285267363556186, 5.072588333338042, 5.285267363556186,
               0.16731709090652816, 0.11535862514214866, 0.19876709346550517, 0.18481508889880247,
               0.40340447010462394, 0.17230458310796753],
  "effort": [0.4323760465593156, -0.20044753532976928, 0.1504599367865372, 0.21867237519140112,
             0.03165760820698054, -0.03362293003986821, 0.06843869610812457, 0.08469658831800274,
             0.04200683552587098, 0.10117358974678807]
}
```

`backend/ros2_translate.py` looks these up **by name**
(`backend.config.ROS2_WHEEL_JOINT_NAMES`/`ROS2_ARM_JOINT_NAMES`), not list
position — the wheel and arm name blocks can arrive in any relative order.

### `/imu/data` — `Imu`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": "imu_link"},
  "orientation": {"x": 0.0, "y": 0.0, "z": 0.0066927313833479675, "w": 0.9999776034225119},
  "orientation_covariance": [0.0001, 0.0, 0.0, 0.0, 0.0001, 0.0, 0.0, 0.0, 0.0001],
  "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.03596840363685026},
  "angular_velocity_covariance": [0.0001, 0.0, 0.0, 0.0, 0.0001, 0.0, 0.0, 0.0, 0.0001],
  "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.782036247665252},
  "linear_acceleration_covariance": [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
}
```

### `/tf` — `TFMessage`

```json
{
  "transforms": [
    {
      "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": "odom"},
      "child_frame_id": "base_footprint",
      "transform": {
        "translation": {"x": 0.1488450843434255, "y": 0.0005961686414966519, "z": 0.0},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0066927313833479675, "w": 0.9999776034225119}
      }
    },
    {
      "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": "arm_base_link"},
      "child_frame_id": "gripper_link",
      "transform": {
        "translation": {"x": 0.378769388675768, "y": 0.01896962402168094, "z": 0.1393062877409643},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
      }
    }
  ]
}
```

### `/tf_static` — `TFMessage`

```json
{
  "transforms": [
    {
      "header": {"stamp": {"sec": 1791920191, "nanosec": 984950066}, "frame_id": "base_link"},
      "child_frame_id": "imu_link",
      "transform": {
        "translation": {"x": 0.0, "y": 0.0, "z": 0.05},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
      }
    },
    {
      "header": {"stamp": {"sec": 1791920191, "nanosec": 984950066}, "frame_id": "base_link"},
      "child_frame_id": "arm_base_link",
      "transform": {
        "translation": {"x": 0.1, "y": 0.0, "z": 0.1},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
      }
    }
  ]
}
```

### `/arm_controller/joint_trajectory` — `JointTrajectory`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": ""},
  "joint_names": ["waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"],
  "points": [
    {
      "positions": [0.08350386057603926, 0.05763801520611251, 0.09947595486594192,
                    0.09270509831248422, 0.20336832153790008, 0.08816778784387097],
      "velocities": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      "accelerations": [],
      "effort": [],
      "time_from_start": {"sec": 0, "nanosec": 300000000}
    }
  ]
}
```

### `/arm_controller/controller_state` — `JointTrajectoryControllerState`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 835943937}, "frame_id": ""},
  "joint_names": ["waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"],
  "desired": {
    "positions": [0.08350386057603926, 0.05763801520611251, 0.09947595486594192,
                  0.09270509831248422, 0.20336832153790008, 0.08816778784387097],
    "velocities": [], "accelerations": [], "effort": [], "time_from_start": {"sec": 0, "nanosec": 0}
  },
  "actual": {
    "positions": [0.05004044239473364, 0.03456629017768277, 0.0597225361728409,
                  0.05574208053272374, 0.12268742751697531, 0.05370687122227748],
    "velocities": [0.16731709090652816, 0.11535862514214866, 0.19876709346550517,
                   0.18481508889880247, 0.40340447010462394, 0.17230458310796753],
    "accelerations": [],
    "effort": [0.03165760820698054, -0.03362293003986821, 0.06843869610812457,
               0.08469658831800274, 0.04200683552587098, 0.10117358974678807],
    "time_from_start": {"sec": 0, "nanosec": 0}
  },
  "error": {
    "positions": [0.03346341818130562, 0.02307172502842974, 0.03975341869310102,
                  0.03696301777976048, 0.08068089402092476, 0.03446091662159349],
    "velocities": [], "accelerations": [], "effort": [], "time_from_start": {"sec": 0, "nanosec": 0}
  }
}
```

### `/camera/image_raw`, `/camera/image_color`, `/camera/image_rect`, `/camera/image_rect_color` — `Image`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 941604137}, "frame_id": "camera_link"},
  "height": 48,
  "width": 64,
  "encoding": "rgb8",
  "is_bigendian": 0,
  "step": 192,
  "data": "Pi7ixeCp/EgursBXhDTepF21...<12288 base64 chars for image_raw/image_color/image_rect_color's rgb8; image_rect uses mono8 and is shorter>"
}
```

### `/camera/camera_info` — `CameraInfo`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 941604137}, "frame_id": "camera_link"},
  "height": 48,
  "width": 64,
  "distortion_model": "plumb_bob",
  "d": [0.0, 0.0, 0.0, 0.0, 0.0],
  "k": [64.0, 0.0, 32.0, 0.0, 64.0, 24.0, 0.0, 0.0, 1.0],
  "r": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
  "p": [64.0, 0.0, 32.0, 0.0, 0.0, 64.0, 24.0, 0.0, 0.0, 0.0, 1.0, 0.0],
  "binning_x": 0,
  "binning_y": 0,
  "roi": {"x_offset": 0, "y_offset": 0, "height": 0, "width": 0, "do_rectify": false}
}
```

`k`/`p`'s focal length and principal point are placeholder values derived
from the synthetic resolution (`fx=fy=width`, `cx=width/2`, `cy=height/2`)
— not a real calibration.

### `/camera/image_color/compressed`, `/camera/image_rect_color/compressed` — `CompressedImage`

```json
{
  "header": {"stamp": {"sec": 1791920178, "nanosec": 941604137}, "frame_id": "camera_link"},
  "format": "png",
  "data": "iVBORw0KGgoAAAANSUhEUgAA...<12444 base64 chars total, a real PNG via ros2_sim/png_encode.py>"
}
```

Unlike `Image.data` (raw pixels), `data` here decodes (via base64) to an
actual, valid, browser-decodable PNG file — `ros2_sim/png_encode.py` is a
minimal stdlib (`zlib`+`struct`) encoder, no Pillow/OpenCV dependency.
`format` says `"png"`; real ROS 2 camera drivers more commonly say
`"jpeg"`, but JPEG isn't practical to encode from the standard library
alone.

# Related

* [ROS 2 bridge (simulated)](../components/ros2-bridge.md)
* [Backend](../components/backend.md) — subscribes to `cmd_vel`, `joint_states`, `imu/data`, `arm_controller/controller_state`, and `camera/image_color/compressed` directly.
* [Dashboard](../components/dashboard.md)
* [WebSocket stream](websocket-stream.md) — the `camera_frame` frame type `camera/image_color/compressed` turns into.
* [MQTT external-emulator topics](mqtt-external.md) — the older, flat-schema ROS 2 emulation on the `rover/#` tree; a different, unrelated mechanism from this bridge.
