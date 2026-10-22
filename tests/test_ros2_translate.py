from backend import ros2_translate


def _as_dict(pairs: list[tuple[str, dict]]) -> dict[str, dict]:
    return dict(pairs)


def test_cmd_vel_updates_last_commanded_velocity_used_by_joint_states():
    ros2_translate.translate("cmd_vel", {"linear": {"x": 0.4, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.0}})
    out = _as_dict(
        ros2_translate.translate(
            "joint_states",
            {
                "header": {"stamp": {"sec": 1, "nanosec": 0}, "frame_id": ""},
                "name": ["wheel_FL_joint"],
                "position": [0.0],
                "velocity": [0.4 / 0.075],
                "effort": [0.1],
            },
        )
    )
    assert out["wheels/fl/speed"]["value"]["commanded"] == out["wheels/fl/speed"]["value"]["actual"]
    assert out["wheels/fl/slip"]["value"] == 0.0


def test_joint_states_separates_wheel_and_arm_joints_regardless_of_order():
    """Regression test: /joint_states carries wheel + arm joints in one
    message, and must be looked up by name -- not list position -- or an
    arm joint's value silently overwrites a wheel's point (or vice versa)."""
    payload = {
        "header": {"stamp": {"sec": 2, "nanosec": 0}, "frame_id": ""},
        # Deliberately NOT wheels-then-arm, to prove name lookup (not index) is used.
        "name": ["gripper", "wheel_RR_joint", "waist", "wheel_FL_joint"],
        "position": [-0.05, 1.5, 0.2, 1.4],
        "velocity": [0.0, 3.0, 0.0, 2.9],
        "effort": [0.01, 0.28, 0.02, 0.30],
    }
    out = _as_dict(ros2_translate.translate("joint_states", payload))

    # wheel_RR_joint -> index 3 ("rr"), picks up ITS OWN position/effort, not gripper's or waist's.
    assert out["joints/3/position"]["value"] == 1.5
    assert out["joints/3/torque"]["value"] == 0.28

    # wheel_FL_joint -> index 0 ("fl").
    assert out["joints/0/position"]["value"] == 1.4
    assert out["joints/0/torque"]["value"] == 0.30

    # Arm joints land under arm/<name>/..., untouched by the wheel index scheme.
    assert out["arm/gripper/position"]["value"] == -0.05
    assert out["arm/gripper/effort"]["value"] == 0.01
    assert out["arm/waist/position"]["value"] == 0.2
    assert out["arm/waist/effort"]["value"] == 0.02

    # No cross-contamination: nothing named "arm/wheel_*" or "joints/*" for the arm joints.
    assert "joints/1/position" not in out or out["joints/1/position"]["value"] != -0.05


def test_imu_data_translation():
    out = _as_dict(
        ros2_translate.translate(
            "imu/data",
            {
                "header": {"stamp": {"sec": 3, "nanosec": 0}, "frame_id": "imu_link"},
                "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.1},
                "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.81},
            },
        )
    )
    assert out["imu/orientation"]["value"] == {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}
    assert out["imu/accel"]["value"] == {"x": 0.0, "y": 0.0, "z": 9.81}
    assert out["imu/gyro"]["value"] == {"x": 0.0, "y": 0.0, "z": 0.1}


def test_arm_controller_state_translation():
    out = _as_dict(
        ros2_translate.translate(
            "arm_controller/controller_state",
            {
                "header": {"stamp": {"sec": 4, "nanosec": 0}, "frame_id": ""},
                "joint_names": ["waist", "shoulder"],
                "desired": {"positions": [0.2, 0.1]},
                "actual": {"positions": [0.18, 0.11]},
                "error": {"positions": [0.02, -0.01]},
            },
        )
    )
    assert out["arm/waist/error"]["value"] == 0.02
    assert out["arm/shoulder/error"]["value"] == -0.01


def test_unknown_topic_returns_only_heartbeat():
    out = ros2_translate.translate("some/unhandled/topic", {})
    assert [p[0] for p in out] == ["comms/heartbeat"]
