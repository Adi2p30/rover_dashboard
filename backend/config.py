"""Static config: broker address, ports, and per-point detector thresholds."""
from __future__ import annotations

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_SUBSCRIBE_TOPIC = "rover/#"
SAFE_STATE_TOPIC = "rover/command/safe_state"

# The one camera feed shown live on the dashboard. mqtt_bridge.py special-
# cases this topic -- a frame is broadcast straight to WebSocket clients as
# a "camera_frame" message, bypassing state_store/fault detection (images
# aren't scalar points, and state_store's history buffer isn't meant to
# hold HISTORY_MAXLEN frames' worth of image bytes per client snapshot).
ROS2_CAMERA_TOPIC = "camera/image_color/compressed"

# ros2_sim publishes real ROS 2 topic names (leading "/" stripped for MQTT)
# outside the rover/# tree -- these need their own explicit subscriptions,
# and backend.ros2_translate turns each into rover/* point payloads.
# ros2_sim also publishes /heading_controller/cmd_vel, /merged_odom,
# /wheel_odom, /tf(_static), and the other 7 /camera/* topics -- those
# aren't translated (no point schema slot, or not worth a dashboard panel),
# so the backend never subscribes to them.
ROS2_SIM_TOPICS = ["cmd_vel", "joint_states", "imu/data", "arm_controller/controller_state", ROS2_CAMERA_TOPIC]

# Robot geometry (matches ros2_sim/fake_robot.py's own constants) -- needed
# to turn /cmd_vel into commanded per-wheel speeds for the slip calculation.
WHEEL_RADIUS_M = 0.075
TRACK_WIDTH_M = 0.34

# /joint_states carries wheel joints AND arm joints in one message (a real
# joint_state_publisher would aggregate both subsystems the same way) --
# ros2_translate.py looks wheel joints up by name, not position, so this
# dict (not a positional list) is what ties a wheel_FL_joint-shaped name
# back to this project's "fl"/"fr"/"rl"/"rr" wheel/point ids.
ROS2_WHEEL_JOINT_NAMES = {
    "wheel_FL_joint": "fl",
    "wheel_FR_joint": "fr",
    "wheel_RL_joint": "rl",
    "wheel_RR_joint": "rr",
}

# The "joints/<i>/..." point ids predate wheel-by-name lookup and are kept
# stable (0=fl, 1=fr, 2=rl, 3=rr) so the dashboard's existing Joints panel
# doesn't need to change when /joint_states also carries arm joints.
ROS2_JOINT_INDEX = {"fl": 0, "fr": 1, "rl": 2, "rr": 3}

# ros2_sim/fake_robot.py's ARM_JOINT_NAMES (WidowX AI) -- any /joint_states
# name not in ROS2_WHEEL_JOINT_NAMES and not here is ignored by ros2_translate.
ROS2_ARM_JOINT_NAMES = ["waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"]

# Topics under this prefix carry generator/pipeline status, not telemetry
# points -- the backend relays them as "log" WebSocket frames instead of
# running them through state_store/fault detection.
LOG_TOPIC_PREFIX = "rover/log/"

HTTP_PORT = 8000

HISTORY_MAXLEN = 300

# point_id -> list of (detector_type, kwargs)
# detector_type in {"threshold", "zscore", "rate_of_change", "staleness"}
#
# No ros2_sim source exists for joint temperature or GPS (neither is a real
# ROS 2 topic this simulator publishes), so there's no detector config for
# them -- a staleness detector on a point nothing ever publishes would
# immediately report "never seen" and fault forever. Same reasoning covers
# battery/* and arm/*: ros2_sim no longer publishes /battery at all (there's
# no real BatteryState-equivalent topic in the Leo Rover 1.9 / WidowX AI
# reference topic list this project now follows), and arm/*/position|effort
# don't have tuned thresholds yet.
#
# joints/*/position has no rate_of_change detector: it's a continuously
# spinning wheel joint wrapping mod 2*pi, so it jumps every revolution --
# that wrap is normal, not a fault.
DETECTOR_CONFIG: dict[str, list[dict]] = {
    "joints/0/torque": [{"type": "zscore", "warn_z": 3.0, "fault_z": 5.0}],
    "joints/1/torque": [{"type": "zscore", "warn_z": 3.0, "fault_z": 5.0}],
    "joints/2/torque": [{"type": "zscore", "warn_z": 3.0, "fault_z": 5.0}],
    "joints/3/torque": [{"type": "zscore", "warn_z": 3.0, "fault_z": 5.0}],
    "wheels/fl/slip": [{"type": "threshold", "warn_hi": 0.3, "fault_hi": 0.7, "hysteresis": 0.05}],
    "wheels/fr/slip": [{"type": "threshold", "warn_hi": 0.3, "fault_hi": 0.7, "hysteresis": 0.05}],
    "wheels/rl/slip": [{"type": "threshold", "warn_hi": 0.3, "fault_hi": 0.7, "hysteresis": 0.05}],
    "wheels/rr/slip": [{"type": "threshold", "warn_hi": 0.3, "fault_hi": 0.7, "hysteresis": 0.05}],
    "comms/heartbeat": [{"type": "staleness", "warn_timeout": 3.0, "fault_timeout": 8.0}],
    "imu/orientation": [{"type": "staleness", "warn_timeout": 3.0, "fault_timeout": 8.0}],
}
