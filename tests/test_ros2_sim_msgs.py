import dataclasses

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
    from_dict,
)


def roundtrip(msg):
    data = dataclasses.asdict(msg)
    return from_dict(type(msg), data)


def test_twist_roundtrip():
    msg = Twist(linear=Vector3(x=0.35, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=-0.2))
    assert roundtrip(msg) == msg


def test_odometry_roundtrip_nested_and_covariance():
    msg = Odometry(
        header=Header(stamp=Time(sec=1, nanosec=500), frame_id="odom"),
        child_frame_id="base_footprint",
        pose=PoseWithCovariance(
            pose=Pose(position=Point(x=2.1, y=0.8, z=0.0), orientation=Quaternion(x=0, y=0, z=0.26, w=0.97)),
            covariance=[0.01] * 36,
        ),
        twist=TwistWithCovariance(twist=Twist(linear=Vector3(x=0.35)), covariance=[0.001] * 36),
    )
    out = roundtrip(msg)
    assert out == msg
    assert isinstance(out.pose, PoseWithCovariance)
    assert isinstance(out.pose.pose.position, Point)
    assert len(out.pose.covariance) == 36


def test_joint_state_roundtrip_lists():
    msg = JointState(
        header=Header(frame_id=""),
        name=["wheel_FL_joint", "wheel_FR_joint", "waist", "gripper"],
        position=[12.45, 12.38, 0.1, -0.05],
        velocity=[1.2, 1.2, 0.0, 0.0],
        effort=[0.15, 0.14, 0.02, 0.01],
    )
    assert roundtrip(msg) == msg


def test_imu_roundtrip():
    msg = Imu(
        header=Header(frame_id="imu_link"),
        orientation=Quaternion(x=0.002, y=-0.001, z=0.26, w=0.97),
        orientation_covariance=[0.0001] * 9,
        angular_velocity=Vector3(z=-0.2),
        angular_velocity_covariance=[0.0001] * 9,
        linear_acceleration=Vector3(z=9.81),
        linear_acceleration_covariance=[0.001] * 9,
    )
    assert roundtrip(msg) == msg


def test_tf_message_roundtrip():
    msg = TFMessage(
        transforms=[
            TransformStamped(
                header=Header(frame_id="odom"),
                child_frame_id="base_footprint",
                transform=Transform(translation=Vector3(x=1.0), rotation=Quaternion()),
            )
        ]
    )
    out = roundtrip(msg)
    assert out == msg
    assert isinstance(out.transforms[0], TransformStamped)


def test_from_dict_ignores_missing_fields_and_uses_defaults():
    out = from_dict(Twist, {"linear": {"x": 1.0, "y": 0.0, "z": 0.0}})
    assert out.linear == Vector3(x=1.0)
    assert out.angular == Vector3()


def test_image_roundtrip():
    msg = Image(
        header=Header(frame_id="camera_link"),
        height=48,
        width=64,
        encoding="rgb8",
        is_bigendian=0,
        step=64 * 3,
        data="QUJD",  # base64 for b"ABC", just needs to be a string that survives the roundtrip
    )
    assert roundtrip(msg) == msg


def test_camera_info_roundtrip_nested_roi():
    msg = CameraInfo(
        header=Header(frame_id="camera_link"),
        height=48,
        width=64,
        distortion_model="plumb_bob",
        d=[0.0] * 5,
        k=[64.0, 0.0, 32.0, 0.0, 64.0, 24.0, 0.0, 0.0, 1.0],
        r=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        p=[64.0, 0.0, 32.0, 0.0, 0.0, 64.0, 24.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        binning_x=0,
        binning_y=0,
        roi=RegionOfInterest(x_offset=1, y_offset=2, height=10, width=10, do_rectify=True),
    )
    out = roundtrip(msg)
    assert out == msg
    assert isinstance(out.roi, RegionOfInterest)


def test_compressed_image_roundtrip():
    msg = CompressedImage(header=Header(frame_id="camera_link"), format="png", data="iVBORw0KGgo=")
    assert roundtrip(msg) == msg


def test_joint_trajectory_roundtrip_nested_points():
    msg = JointTrajectory(
        header=Header(frame_id=""),
        joint_names=["waist", "shoulder"],
        points=[
            JointTrajectoryPoint(
                positions=[0.1, 0.2], velocities=[0.0, 0.0], time_from_start=Duration(sec=0, nanosec=300_000_000)
            )
        ],
    )
    out = roundtrip(msg)
    assert out == msg
    assert isinstance(out.points[0], JointTrajectoryPoint)
    assert isinstance(out.points[0].time_from_start, Duration)


def test_joint_trajectory_controller_state_roundtrip():
    msg = JointTrajectoryControllerState(
        header=Header(frame_id=""),
        joint_names=["waist", "shoulder"],
        desired=JointTrajectoryPoint(positions=[0.1, 0.2]),
        actual=JointTrajectoryPoint(positions=[0.08, 0.19]),
        error=JointTrajectoryPoint(positions=[0.02, 0.01]),
    )
    out = roundtrip(msg)
    assert out == msg
    assert isinstance(out.desired, JointTrajectoryPoint)
    assert isinstance(out.actual, JointTrajectoryPoint)
    assert isinstance(out.error, JointTrajectoryPoint)
