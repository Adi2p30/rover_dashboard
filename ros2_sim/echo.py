"""Example subscriber over the simulated bridge: subscribes to the given
topics (default: all of them) and prints every message as it arrives,
the same way `ros2 topic echo` would for a real node. This is the
"interface to subscribe to those topics" -- node.create_subscription(...)
below is the whole API surface a real subscriber needs.

Usage:
    python -m ros2_sim.echo                      # echo everything
    python -m ros2_sim.echo /cmd_vel /imu/data    # echo just these topics
"""
from __future__ import annotations

import argparse
import time

from ros2_sim.msgs import (
    CameraInfo,
    CompressedImage,
    Image,
    Imu,
    JointState,
    JointTrajectory,
    JointTrajectoryControllerState,
    Odometry,
    TFMessage,
    Twist,
)
from ros2_sim.node import DEFAULT_BROKER_HOST, DEFAULT_BROKER_PORT, Node

TOPICS: dict[str, type] = {
    "/cmd_vel": Twist,
    "/heading_controller/cmd_vel": Twist,
    "/merged_odom": Odometry,
    "/wheel_odom": Odometry,
    "/joint_states": JointState,
    "/imu/data": Imu,
    "/tf": TFMessage,
    "/tf_static": TFMessage,
    "/arm_controller/joint_trajectory": JointTrajectory,
    "/arm_controller/controller_state": JointTrajectoryControllerState,
    "/camera/image_raw": Image,
    "/camera/camera_info": CameraInfo,
    "/camera/image_color": Image,
    "/camera/image_color/compressed": CompressedImage,
    "/camera/image_mono": Image,
    "/camera/image_rect": Image,
    "/camera/image_rect_color": Image,
    "/camera/image_rect_color/compressed": CompressedImage,
}


def _print_handler(topic: str):
    def handler(msg) -> None:
        print(f"[{topic}] {msg}")

    return handler


def run(topics: list[str], broker_host: str, broker_port: int) -> None:
    node = Node("echo", broker_host, broker_port)
    for topic in topics:
        msg_type = TOPICS[topic]
        node.create_subscription(msg_type, topic, _print_handler(topic))
        print(f"[ros2sim:echo] subscribed to {topic} ({msg_type.__name__})")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Echo messages from the simulated ROS 2 bridge")
    parser.add_argument("topics", nargs="*", help=f"topics to echo (default: all of {', '.join(TOPICS)})")
    parser.add_argument("--broker-host", default=DEFAULT_BROKER_HOST)
    parser.add_argument("--broker-port", type=int, default=DEFAULT_BROKER_PORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topics = args.topics or list(TOPICS)
    unknown = [t for t in topics if t not in TOPICS]
    if unknown:
        raise SystemExit(f"unknown topic(s): {unknown}; choose from {list(TOPICS)}")
    run(topics, args.broker_host, args.broker_port)


if __name__ == "__main__":
    main()
