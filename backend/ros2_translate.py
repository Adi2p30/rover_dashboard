"""Translates ros2_sim's real-ROS2-shaped MQTT messages into this project's
rover/* point_id -> {"ts", "value"} schema, so state_store, the fault
detectors, and the dashboard charts work exactly as they would against a
real ROS 2-to-MQTT bridge -- they never see a ROS 2 message shape.

Only cmd_vel, joint_states, imu/data, and arm_controller/controller_state
carry data the existing point schema has a slot for; heading_controller/
cmd_vel, merged_odom/wheel_odom/tf(_static), and most /camera/* aren't
translated (see backend.config.ROS2_SIM_TOPICS for the subscribed topic
list -- the one camera topic there is handled separately in
backend.mqtt_bridge, not here, since it isn't a scalar point).

/joint_states carries BOTH wheel and arm joints in one message (ros2_sim
publishes one combined JointState the way a real joint_state_publisher
would). Joints are looked up by name, not list position -- the two
subsystems' joints can arrive in any order, and naively indexing into
position/velocity/effort by 0..3 would silently mix an arm joint's value
into a wheel's point (or vice versa) the moment the name list isn't
wheels-then-arm."""
from __future__ import annotations

import math
import time

from backend.config import ROS2_ARM_JOINT_NAMES, ROS2_JOINT_INDEX, ROS2_WHEEL_JOINT_NAMES, TRACK_WIDTH_M, WHEEL_RADIUS_M

# Latest commanded velocity, used to derive per-wheel commanded speed when a
# /joint_states message reports actual velocity. cmd_vel has no header/stamp
# of its own to key this off of, so it's just the most recent value seen.
_last_cmd_vel = {"linear_x": 0.0, "angular_z": 0.0}


def _stamp_to_ts(header: dict | None, default: float) -> float:
    if not header:
        return default
    stamp = header.get("stamp")
    if not stamp or stamp.get("sec") is None:
        return default
    return stamp["sec"] + stamp.get("nanosec", 0) / 1e9


def _quaternion_to_yaw(q: dict) -> float:
    return math.atan2(2.0 * (q["w"] * q["z"] + q["x"] * q["y"]), 1.0 - 2.0 * (q["y"] ** 2 + q["z"] ** 2))


def _commanded_wheel_speeds() -> dict[str, float]:
    linear_x = _last_cmd_vel["linear_x"]
    angular_z = _last_cmd_vel["angular_z"]
    left = (linear_x - angular_z * TRACK_WIDTH_M / 2.0) / WHEEL_RADIUS_M
    right = (linear_x + angular_z * TRACK_WIDTH_M / 2.0) / WHEEL_RADIUS_M
    return {"fl": left, "fr": right, "rl": left, "rr": right}


def translate(topic: str, payload: dict) -> list[tuple[str, dict]]:
    """topic is the raw ros2_sim MQTT topic with its leading '/' already
    stripped (e.g. 'imu/data', 'joint_states'). Returns (point_id, {"ts",
    "value"}) pairs to feed through state_store/fault detection."""
    now = time.time()
    # Any ROS 2 message arriving at all is legitimate evidence of comms liveness.
    out: list[tuple[str, dict]] = [("comms/heartbeat", {"ts": now, "value": now})]

    if topic == "cmd_vel":
        _last_cmd_vel["linear_x"] = payload["linear"]["x"]
        _last_cmd_vel["angular_z"] = payload["angular"]["z"]
        return out

    if topic == "joint_states":
        ts = _stamp_to_ts(payload.get("header"), now)
        commanded = _commanded_wheel_speeds()
        names = payload["name"]
        for i, name in enumerate(names):
            position = payload["position"][i]
            velocity = payload["velocity"][i]
            effort = payload["effort"][i]

            wid = ROS2_WHEEL_JOINT_NAMES.get(name)
            if wid is not None:
                idx = ROS2_JOINT_INDEX[wid]
                out.append((f"joints/{idx}/position", {"ts": ts, "value": position}))
                out.append((f"joints/{idx}/torque", {"ts": ts, "value": effort}))
                out.append((f"wheels/{wid}/speed", {"ts": ts, "value": {"commanded": commanded[wid], "actual": velocity}}))
                denom = max(abs(commanded[wid]), 1e-3)
                out.append((f"wheels/{wid}/slip", {"ts": ts, "value": abs(commanded[wid] - velocity) / denom}))
                continue

            if name in ROS2_ARM_JOINT_NAMES:
                out.append((f"arm/{name}/position", {"ts": ts, "value": position}))
                out.append((f"arm/{name}/effort", {"ts": ts, "value": effort}))
        return out

    if topic == "imu/data":
        ts = _stamp_to_ts(payload.get("header"), now)
        yaw = _quaternion_to_yaw(payload["orientation"])
        av, la = payload["angular_velocity"], payload["linear_acceleration"]
        # fake_robot.py's quaternion only ever encodes yaw, so roll/pitch are 0.
        out.append(("imu/orientation", {"ts": ts, "value": {"roll": 0.0, "pitch": 0.0, "yaw": math.degrees(yaw)}}))
        out.append(("imu/accel", {"ts": ts, "value": {"x": la["x"], "y": la["y"], "z": la["z"]}}))
        out.append(("imu/gyro", {"ts": ts, "value": {"x": av["x"], "y": av["y"], "z": av["z"]}}))
        return out

    if topic == "arm_controller/controller_state":
        ts = _stamp_to_ts(payload.get("header"), now)
        names = payload["joint_names"]
        error_positions = payload["error"]["positions"]
        for i, name in enumerate(names):
            out.append((f"arm/{name}/error", {"ts": ts, "value": error_positions[i]}))
        return out

    return out
