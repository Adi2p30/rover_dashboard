"""Message dataclasses for the topics this simulated bridge carries, shaped
to match the real ROS 2 message definitions field-for-field (geometry_msgs,
nav_msgs, sensor_msgs, trajectory_msgs, control_msgs, tf2_msgs) so a
subscriber callback sees the same attributes a real rclpy subscription
would hand it.

Image/CompressedImage/CameraInfo carry their byte-array fields (`data`) as
base64 strings rather than `bytes` -- JSON has no byte-array type, and this
matches the convention rosbridge_suite/roslibjs already use when putting a
ROS 2 byte array on the wire as JSON. Frames are a small synthetic
placeholder resolution (see ros2_sim/fake_robot.py's CAMERA_WIDTH/HEIGHT),
not the real Arducam IMX477's native resolution -- this is still a
telemetry-sized JSON/MQTT pipeline, not a real streaming transport.

JointTrajectoryControllerState only models `desired`/`actual`/`error` --
the real message (control_msgs, Humble+) also has `reference`/`feedback`/
`output` (newer aliases layered on for API continuity) and `multi_dof_*`
fields for Cartesian control, neither of which this single-arm,
joint-space simulation produces.
"""
from __future__ import annotations

import dataclasses
import typing
from dataclasses import dataclass, field


@dataclass
class Time:
    sec: int = 0
    nanosec: int = 0


@dataclass
class Header:
    stamp: Time = field(default_factory=Time)
    frame_id: str = ""


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Quaternion:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


@dataclass
class Twist:
    linear: Vector3 = field(default_factory=Vector3)
    angular: Vector3 = field(default_factory=Vector3)


@dataclass
class Pose:
    position: Point = field(default_factory=Point)
    orientation: Quaternion = field(default_factory=Quaternion)


@dataclass
class PoseWithCovariance:
    pose: Pose = field(default_factory=Pose)
    covariance: list[float] = field(default_factory=list)  # 6x6, row-major


@dataclass
class TwistWithCovariance:
    twist: Twist = field(default_factory=Twist)
    covariance: list[float] = field(default_factory=list)  # 6x6, row-major


@dataclass
class Odometry:
    """nav_msgs/msg/Odometry -- used for /odom, /merged_odom, /wheel_odom."""

    header: Header = field(default_factory=Header)
    child_frame_id: str = ""
    pose: PoseWithCovariance = field(default_factory=PoseWithCovariance)
    twist: TwistWithCovariance = field(default_factory=TwistWithCovariance)


@dataclass
class JointState:
    """sensor_msgs/msg/JointState -- used for /joint_states."""

    header: Header = field(default_factory=Header)
    name: list[str] = field(default_factory=list)
    position: list[float] = field(default_factory=list)
    velocity: list[float] = field(default_factory=list)
    effort: list[float] = field(default_factory=list)


@dataclass
class Imu:
    """sensor_msgs/msg/Imu -- used for /imu/data."""

    header: Header = field(default_factory=Header)
    orientation: Quaternion = field(default_factory=Quaternion)
    orientation_covariance: list[float] = field(default_factory=list)  # 3x3
    angular_velocity: Vector3 = field(default_factory=Vector3)
    angular_velocity_covariance: list[float] = field(default_factory=list)  # 3x3
    linear_acceleration: Vector3 = field(default_factory=Vector3)
    linear_acceleration_covariance: list[float] = field(default_factory=list)  # 3x3


@dataclass
class Transform:
    translation: Vector3 = field(default_factory=Vector3)
    rotation: Quaternion = field(default_factory=Quaternion)


@dataclass
class TransformStamped:
    header: Header = field(default_factory=Header)
    child_frame_id: str = ""
    transform: Transform = field(default_factory=Transform)


@dataclass
class TFMessage:
    """tf2_msgs/msg/TFMessage -- used for /tf, /tf_static."""

    transforms: list[TransformStamped] = field(default_factory=list)


@dataclass
class RegionOfInterest:
    x_offset: int = 0
    y_offset: int = 0
    height: int = 0
    width: int = 0
    do_rectify: bool = False


@dataclass
class Image:
    """sensor_msgs/msg/Image -- used for /camera/image_raw, /image_color,
    /image_mono, /image_rect, /image_rect_color. `data` is base64 (see
    module docstring); `step` is width * bytes-per-pixel for `encoding`."""

    header: Header = field(default_factory=Header)
    height: int = 0
    width: int = 0
    encoding: str = ""
    is_bigendian: int = 0
    step: int = 0
    data: str = ""


@dataclass
class CameraInfo:
    """sensor_msgs/msg/CameraInfo -- used for /camera/camera_info."""

    header: Header = field(default_factory=Header)
    height: int = 0
    width: int = 0
    distortion_model: str = "plumb_bob"
    d: list[float] = field(default_factory=list)
    k: list[float] = field(default_factory=list)  # 3x3, row-major
    r: list[float] = field(default_factory=list)  # 3x3, row-major
    p: list[float] = field(default_factory=list)  # 3x4, row-major
    binning_x: int = 0
    binning_y: int = 0
    roi: RegionOfInterest = field(default_factory=RegionOfInterest)


@dataclass
class CompressedImage:
    """sensor_msgs/msg/CompressedImage -- used for
    /camera/image_color/compressed, /camera/image_rect_color/compressed.
    `format` is "png" here (a real PNG, stdlib-encoded -- see
    ros2_sim/png_encode.py); real ROS 2 drivers more commonly say "jpeg"."""

    header: Header = field(default_factory=Header)
    format: str = "png"
    data: str = ""


@dataclass
class Duration:
    """builtin_interfaces/msg/Duration -- structurally identical to Time,
    kept as its own type to match the real message graph."""

    sec: int = 0
    nanosec: int = 0


@dataclass
class JointTrajectoryPoint:
    positions: list[float] = field(default_factory=list)
    velocities: list[float] = field(default_factory=list)
    accelerations: list[float] = field(default_factory=list)
    effort: list[float] = field(default_factory=list)
    time_from_start: Duration = field(default_factory=Duration)


@dataclass
class JointTrajectory:
    """trajectory_msgs/msg/JointTrajectory -- used for
    /arm_controller/joint_trajectory."""

    header: Header = field(default_factory=Header)
    joint_names: list[str] = field(default_factory=list)
    points: list[JointTrajectoryPoint] = field(default_factory=list)


@dataclass
class JointTrajectoryControllerState:
    """control_msgs/msg/JointTrajectoryControllerState -- used for
    /arm_controller/controller_state. See module docstring for the real
    fields this deliberately omits."""

    header: Header = field(default_factory=Header)
    joint_names: list[str] = field(default_factory=list)
    desired: JointTrajectoryPoint = field(default_factory=JointTrajectoryPoint)
    actual: JointTrajectoryPoint = field(default_factory=JointTrajectoryPoint)
    error: JointTrajectoryPoint = field(default_factory=JointTrajectoryPoint)


def from_dict(cls: type, data: dict):
    """Reconstruct a (possibly nested) dataclass instance from a plain dict,
    the inverse of dataclasses.asdict(). Used on the subscriber side to turn
    a JSON payload back into a typed message object."""
    if not dataclasses.is_dataclass(cls):
        return data
    kwargs = {}
    hints = typing.get_type_hints(cls)
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        kwargs[f.name] = _coerce(hints[f.name], data[f.name])
    return cls(**kwargs)


def _coerce(tp, value):
    if value is None:
        return value
    origin = typing.get_origin(tp)
    if origin in (list, typing.List):
        (item_type,) = typing.get_args(tp)
        return [_coerce(item_type, v) for v in value]
    if dataclasses.is_dataclass(tp):
        return from_dict(tp, value)
    return value
