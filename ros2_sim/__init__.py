"""Simulated ROS 2 -> MQTT bridge: a fake rclpy-shaped pub/sub interface
(see ros2_sim.node.Node) plus the message dataclasses it carries
(ros2_sim.msgs), backed by this repo's existing Mosquitto broker.

This is NOT a real ROS 2 client -- there's no rclpy and no DDS involved.
It exists so code can be written against something that looks and reads
like a real ROS 2 node (node.create_subscription(Twist, "/cmd_vel", cb)),
while a real rover's actual ROS 2 graph is swapped in later without
touching the subscriber code.
"""
