"""Simulates the robot side of a ROS 2 bridge: publishes synthetic rover,
camera, and arm telemetry using the fake ros2_sim.node.Node API -- the same
message shapes a real ROS 2-to-MQTT bridge would produce from an actual
Leo Rover 1.9 (+ Arducam IMX477 camera, + WidowX AI arm) ROS 2 graph.

Topics published every tick: /cmd_vel, /heading_controller/cmd_vel,
/merged_odom, /wheel_odom, /joint_states (wheel + arm joints combined),
/imu/data, /tf, /arm_controller/joint_trajectory,
/arm_controller/controller_state. /tf_static is published once at startup.
The 8 /camera/* topics publish at a slower, independent rate (every
CAMERA_TICK_DIVISOR ticks) since image payloads are much larger.

/cmd_vel and /arm_controller/joint_trajectory are "Subscribe" topics on a
real rover/arm (something upstream -- teleop, a nav stack, a motion
planner -- publishes commands, and the platform listens). This simulator
has no such upstream node, so it self-publishes synthetic commands on them
too, for the same reason it already self-published /cmd_vel: so
`ros2_sim.echo` (or anything else) has something to observe there.

Usage:
    python -m ros2_sim.fake_robot --rate 10
"""
from __future__ import annotations

import argparse
import base64
import math
import random
import time

import numpy as np

from generator import signals
from ros2_sim.msgs import (
    CameraInfo,
    CompressedImage,
    Duration,
    Header,
    Image,
    Imu,
    JointState,
    JointTrajectory,
    JointTrajectoryControllerState,
    JointTrajectoryPoint,
    Odometry,
    Point,
    Pose,
    PoseWithCovariance,
    Quaternion,
    RegionOfInterest,
    TFMessage,
    Time,
    Transform,
    TransformStamped,
    Twist,
    TwistWithCovariance,
    Vector3,
)
from ros2_sim.node import DEFAULT_BROKER_HOST, DEFAULT_BROKER_PORT, Node
from ros2_sim.png_encode import encode_png

LOG_TOPIC = "rover/log/ros2_sim"

WHEEL_JOINT_NAMES = ["wheel_FL_joint", "wheel_FR_joint", "wheel_RL_joint", "wheel_RR_joint"]
WHEEL_RADIUS_M = 0.075
TRACK_WIDTH_M = 0.34

# WidowX AI joints. Amplitude/period pairs chosen so joints don't all swing
# in lockstep -- there's no real motion-planning goal here, just a plausibly
# busy-looking arm.
ARM_JOINT_NAMES = ["waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"]
ARM_JOINT_AMPLITUDE = [0.6, 0.3, 0.4, 0.3, 0.5, 0.15]
ARM_JOINT_PERIOD = [18.0, 13.0, 10.0, 8.0, 6.0, 4.0]
ARM_ACTUATOR_LAG_S = 0.3  # first-order response time, simulates servo lag behind the commanded trajectory

# Simplified position-only forward kinematics for /tf's arm_base_link ->
# gripper_link transform: waist (yaw) + shoulder/elbow (pitch, planar reach).
# wrist_angle/wrist_rotate/gripper don't move the end-effector position in
# this approximation, only its orientation/grip, which /tf doesn't carry here.
ARM_LINK_SHOULDER_ELBOW_M = 0.15
ARM_LINK_ELBOW_WRIST_M = 0.15
ARM_LINK_WRIST_GRIPPER_M = 0.08
ARM_BASE_HEIGHT_M = 0.12

CAMERA_WIDTH = 64
CAMERA_HEIGHT = 48
CAMERA_TICK_DIVISOR = 5  # publish camera topics on every Nth main-loop tick

POSE_COVARIANCE = [0.01 if i % 7 == 0 else 0.0 for i in range(36)]
TWIST_COVARIANCE = [0.001 if i % 7 == 0 else 0.0 for i in range(36)]
IMU_ORIENT_COV = [0.0001 if i % 4 == 0 else 0.0 for i in range(9)]
IMU_ANGVEL_COV = [0.0001 if i % 4 == 0 else 0.0 for i in range(9)]
IMU_ACCEL_COV = [0.001 if i % 4 == 0 else 0.0 for i in range(9)]


def _stamp(now: float) -> Time:
    sec = int(now)
    return Time(sec=sec, nanosec=int(round((now - sec) * 1e9)))


def _duration(seconds: float) -> Duration:
    sec = int(seconds)
    return Duration(sec=sec, nanosec=int(round((seconds - sec) * 1e9)))


def _quaternion_from_yaw(yaw: float) -> Quaternion:
    return Quaternion(x=0.0, y=0.0, z=math.sin(yaw / 2.0), w=math.cos(yaw / 2.0))


class RoverSim:
    """Leo Rover base: unicycle/skid-steer kinematics driving 4 wheel joints."""

    def __init__(self) -> None:
        self.t = 0.0
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.joint_position = [0.0, 0.0, 0.0, 0.0]
        self.joint_velocity = [0.0, 0.0, 0.0, 0.0]
        self.joint_effort = [0.0, 0.0, 0.0, 0.0]

    def step(self, dt: float) -> None:
        self.t += dt
        self.linear_x = signals.sine_with_noise(self.t, base=0.35, amplitude=0.25, period=12.0, noise_std=0.01)
        self.angular_z = signals.sine_with_noise(self.t, base=0.0, amplitude=0.3, period=16.0, noise_std=0.01)
        self.x += self.linear_x * math.cos(self.yaw) * dt
        self.y += self.linear_x * math.sin(self.yaw) * dt
        self.yaw += self.angular_z * dt

        left = (self.linear_x - self.angular_z * TRACK_WIDTH_M / 2.0) / WHEEL_RADIUS_M
        right = (self.linear_x + self.angular_z * TRACK_WIDTH_M / 2.0) / WHEEL_RADIUS_M
        speeds = [left, right, left, right]
        self.joint_position = [(p + s * dt) % (2 * math.pi) for p, s in zip(self.joint_position, speeds)]
        self.joint_velocity = speeds
        self.joint_effort = [signals.ou_process(e, mean=0.3, theta=0.5, sigma=0.3, dt=dt) for e in self.joint_effort]


class ArmSim:
    """WidowX AI arm: each joint chases a sine-wave commanded trajectory with
    a first-order actuator lag, so /arm_controller/controller_state has a
    non-zero, settling error -- not just desired == actual."""

    def __init__(self) -> None:
        self.t = 0.0
        self.desired = [0.0] * len(ARM_JOINT_NAMES)
        self.actual = [0.0] * len(ARM_JOINT_NAMES)
        self.velocity = [0.0] * len(ARM_JOINT_NAMES)
        self.effort = [0.0] * len(ARM_JOINT_NAMES)

    def step(self, dt: float) -> None:
        self.t += dt
        lag_fraction = min(1.0, dt / ARM_ACTUATOR_LAG_S)
        for i, (amplitude, period) in enumerate(zip(ARM_JOINT_AMPLITUDE, ARM_JOINT_PERIOD)):
            self.desired[i] = signals.sine_with_noise(self.t, base=0.0, amplitude=amplitude, period=period, noise_std=0.0)
            prev_actual = self.actual[i]
            self.actual[i] = prev_actual + (self.desired[i] - prev_actual) * lag_fraction
            self.velocity[i] = (self.actual[i] - prev_actual) / dt
            self.effort[i] = signals.ou_process(self.effort[i], mean=0.2, theta=0.4, sigma=0.15, dt=dt)

    @property
    def error(self) -> list[float]:
        return [d - a for d, a in zip(self.desired, self.actual)]

    def gripper_position(self) -> Point:
        """Simplified position-only FK -- see the ARM_LINK_* comment above."""
        waist, shoulder, elbow = self.actual[0], self.actual[1], self.actual[2]
        reach = (
            ARM_LINK_SHOULDER_ELBOW_M * math.cos(shoulder)
            + ARM_LINK_ELBOW_WRIST_M * math.cos(shoulder + elbow)
            + ARM_LINK_WRIST_GRIPPER_M
        )
        height = ARM_LINK_SHOULDER_ELBOW_M * math.sin(shoulder) + ARM_LINK_ELBOW_WRIST_M * math.sin(shoulder + elbow)
        return Point(x=reach * math.cos(waist), y=reach * math.sin(waist), z=ARM_BASE_HEIGHT_M + height)


class CameraSim:
    """Arducam IMX477: synthetic low-res noise frames, not a real sensor feed
    -- just enough structure (resolution, encoding, a real PNG container)
    for a subscriber or dashboard to render something."""

    def __init__(self) -> None:
        self._rng = np.random.default_rng()

    def rgb_frame(self) -> bytes:
        return self._rng.integers(0, 256, size=(CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8).tobytes()

    @staticmethod
    def to_mono(rgb_bytes: bytes) -> bytes:
        arr = np.frombuffer(rgb_bytes, dtype=np.uint8).reshape(CAMERA_HEIGHT, CAMERA_WIDTH, 3)
        return arr.mean(axis=2).astype(np.uint8).tobytes()


def _image_msg(header: Header, encoding: str, channels: int, pixels: bytes) -> Image:
    return Image(
        header=header,
        height=CAMERA_HEIGHT,
        width=CAMERA_WIDTH,
        encoding=encoding,
        is_bigendian=0,
        step=CAMERA_WIDTH * channels,
        data=base64.b64encode(pixels).decode("ascii"),
    )


def _compressed_image_msg(header: Header, channels: int, pixels: bytes) -> CompressedImage:
    png_bytes = encode_png(CAMERA_WIDTH, CAMERA_HEIGHT, pixels, channels)
    return CompressedImage(header=header, format="png", data=base64.b64encode(png_bytes).decode("ascii"))


def _camera_info_msg(header: Header) -> CameraInfo:
    fx = fy = float(CAMERA_WIDTH)  # placeholder intrinsics, not a real calibration
    cx, cy = CAMERA_WIDTH / 2.0, CAMERA_HEIGHT / 2.0
    return CameraInfo(
        header=header,
        height=CAMERA_HEIGHT,
        width=CAMERA_WIDTH,
        distortion_model="plumb_bob",
        d=[0.0, 0.0, 0.0, 0.0, 0.0],
        k=[fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0],
        r=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        p=[fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0],
        binning_x=0,
        binning_y=0,
        roi=RegionOfInterest(),
    )


def run(rate_hz: float, broker_host: str, broker_port: int) -> None:
    node = Node("fake_rover_bridge", broker_host, broker_port)

    pub_cmd_vel = node.create_publisher(Twist, "/cmd_vel")
    pub_heading_cmd_vel = node.create_publisher(Twist, "/heading_controller/cmd_vel")
    pub_merged_odom = node.create_publisher(Odometry, "/merged_odom")
    pub_wheel_odom = node.create_publisher(Odometry, "/wheel_odom")
    pub_joints = node.create_publisher(JointState, "/joint_states")
    pub_imu = node.create_publisher(Imu, "/imu/data")
    pub_tf = node.create_publisher(TFMessage, "/tf")
    pub_tf_static = node.create_publisher(TFMessage, "/tf_static")
    pub_arm_cmd = node.create_publisher(JointTrajectory, "/arm_controller/joint_trajectory")
    pub_arm_state = node.create_publisher(JointTrajectoryControllerState, "/arm_controller/controller_state")

    pub_image_raw = node.create_publisher(Image, "/camera/image_raw")
    pub_camera_info = node.create_publisher(CameraInfo, "/camera/camera_info")
    pub_image_color = node.create_publisher(Image, "/camera/image_color")
    pub_image_color_compressed = node.create_publisher(CompressedImage, "/camera/image_color/compressed")
    pub_image_mono = node.create_publisher(Image, "/camera/image_mono")
    pub_image_rect = node.create_publisher(Image, "/camera/image_rect")
    pub_image_rect_color = node.create_publisher(Image, "/camera/image_rect_color")
    pub_image_rect_color_compressed = node.create_publisher(CompressedImage, "/camera/image_rect_color/compressed")

    rover = RoverSim()
    arm = ArmSim()
    camera = CameraSim()
    dt = 1.0 / rate_hz
    tick = 0
    tf_static_sent = False
    tx_count = 0
    last_log = time.time()

    print(
        f"[ros2sim:fake_robot] publishing at {rate_hz}Hz on /cmd_vel /heading_controller/cmd_vel /merged_odom "
        "/wheel_odom /joint_states /imu/data /tf /arm_controller/joint_trajectory "
        f"/arm_controller/controller_state, and /camera/* every {CAMERA_TICK_DIVISOR} ticks"
    )

    try:
        while True:
            now = time.time()
            tick += 1
            rover.step(dt)
            arm.step(dt)
            header = Header(stamp=_stamp(now), frame_id="odom")

            cmd_vel_msg = Twist(
                linear=Vector3(x=rover.linear_x, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=rover.angular_z)
            )
            pub_cmd_vel.publish(cmd_vel_msg)
            tx_count += 1
            pub_heading_cmd_vel.publish(cmd_vel_msg)
            tx_count += 1

            odom_msg = Odometry(
                header=header,
                child_frame_id="base_footprint",
                pose=PoseWithCovariance(
                    pose=Pose(position=Point(x=rover.x, y=rover.y, z=0.0), orientation=_quaternion_from_yaw(rover.yaw)),
                    covariance=POSE_COVARIANCE,
                ),
                twist=TwistWithCovariance(
                    twist=Twist(
                        linear=Vector3(x=rover.linear_x, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=rover.angular_z)
                    ),
                    covariance=TWIST_COVARIANCE,
                ),
            )
            pub_merged_odom.publish(odom_msg)
            tx_count += 1
            pub_wheel_odom.publish(odom_msg)
            tx_count += 1

            pub_joints.publish(
                JointState(
                    header=Header(stamp=_stamp(now), frame_id=""),
                    name=list(WHEEL_JOINT_NAMES) + list(ARM_JOINT_NAMES),
                    position=list(rover.joint_position) + list(arm.actual),
                    velocity=list(rover.joint_velocity) + list(arm.velocity),
                    effort=list(rover.joint_effort) + list(arm.effort),
                )
            )
            tx_count += 1

            pub_imu.publish(
                Imu(
                    header=Header(stamp=_stamp(now), frame_id="imu_link"),
                    orientation=_quaternion_from_yaw(rover.yaw),
                    orientation_covariance=IMU_ORIENT_COV,
                    angular_velocity=Vector3(x=0.0, y=0.0, z=rover.angular_z + random.gauss(0, 0.01)),
                    angular_velocity_covariance=IMU_ANGVEL_COV,
                    linear_acceleration=Vector3(x=0.0, y=0.0, z=9.81 + random.gauss(0, 0.02)),
                    linear_acceleration_covariance=IMU_ACCEL_COV,
                )
            )
            tx_count += 1

            pub_tf.publish(
                TFMessage(
                    transforms=[
                        TransformStamped(
                            header=Header(stamp=_stamp(now), frame_id="odom"),
                            child_frame_id="base_footprint",
                            transform=Transform(
                                translation=Vector3(x=rover.x, y=rover.y, z=0.0),
                                rotation=_quaternion_from_yaw(rover.yaw),
                            ),
                        ),
                        TransformStamped(
                            header=Header(stamp=_stamp(now), frame_id="arm_base_link"),
                            child_frame_id="gripper_link",
                            transform=Transform(translation=arm.gripper_position()),
                        ),
                    ]
                )
            )
            tx_count += 1

            if not tf_static_sent:
                pub_tf_static.publish(
                    TFMessage(
                        transforms=[
                            TransformStamped(
                                header=Header(stamp=_stamp(now), frame_id="base_link"),
                                child_frame_id="imu_link",
                                transform=Transform(translation=Vector3(x=0.0, y=0.0, z=0.05)),
                            ),
                            TransformStamped(
                                header=Header(stamp=_stamp(now), frame_id="base_link"),
                                child_frame_id="arm_base_link",
                                transform=Transform(translation=Vector3(x=0.1, y=0.0, z=0.1)),
                            ),
                        ]
                    )
                )
                tf_static_sent = True
                tx_count += 1

            arm_point = JointTrajectoryPoint(
                positions=list(arm.desired), velocities=[0.0] * len(ARM_JOINT_NAMES), time_from_start=_duration(ARM_ACTUATOR_LAG_S)
            )
            pub_arm_cmd.publish(
                JointTrajectory(header=Header(stamp=_stamp(now), frame_id=""), joint_names=list(ARM_JOINT_NAMES), points=[arm_point])
            )
            tx_count += 1

            pub_arm_state.publish(
                JointTrajectoryControllerState(
                    header=Header(stamp=_stamp(now), frame_id=""),
                    joint_names=list(ARM_JOINT_NAMES),
                    desired=JointTrajectoryPoint(positions=list(arm.desired)),
                    actual=JointTrajectoryPoint(positions=list(arm.actual), velocities=list(arm.velocity), effort=list(arm.effort)),
                    error=JointTrajectoryPoint(positions=list(arm.error)),
                )
            )
            tx_count += 1

            if tick % CAMERA_TICK_DIVISOR == 0:
                cam_header = Header(stamp=_stamp(now), frame_id="camera_link")
                rgb = camera.rgb_frame()
                mono = camera.to_mono(rgb)

                pub_image_raw.publish(_image_msg(cam_header, "rgb8", 3, rgb))
                pub_camera_info.publish(_camera_info_msg(cam_header))
                pub_image_color.publish(_image_msg(cam_header, "rgb8", 3, rgb))
                pub_image_color_compressed.publish(_compressed_image_msg(cam_header, 3, rgb))
                pub_image_mono.publish(_image_msg(cam_header, "mono8", 1, mono))
                pub_image_rect.publish(_image_msg(cam_header, "mono8", 1, mono))
                pub_image_rect_color.publish(_image_msg(cam_header, "rgb8", 3, rgb))
                pub_image_rect_color_compressed.publish(_compressed_image_msg(cam_header, 3, rgb))
                tx_count += 8

            if now - last_log >= 1.0:
                print(f"[ros2sim:fake_robot] sent={tx_count}/s pose=(x={rover.x:+.2f},y={rover.y:+.2f})")
                node.publish_status(
                    LOG_TOPIC,
                    {
                        "source": "ros2_sim",
                        "ts": now,
                        "rate": tx_count,
                        "last_topic": "/arm_controller/controller_state",
                        "pose_x": rover.x,
                        "pose_y": rover.y,
                    },
                )
                tx_count = 0
                last_log = now

            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fake ROS 2 rover publishing over the simulated bridge")
    parser.add_argument("--rate", type=float, default=10.0, help="publish rate in Hz")
    parser.add_argument("--broker-host", default=DEFAULT_BROKER_HOST)
    parser.add_argument("--broker-port", type=int, default=DEFAULT_BROKER_PORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.rate, args.broker_host, args.broker_port)


if __name__ == "__main__":
    main()
