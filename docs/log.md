# Directory Update Log

## 2026-10-13
* **Creation**: Adopted the Open Knowledge Format (OKF v0.2) for this project's
  documentation. Established the bundle root at `docs/` with `components/`,
  `interfaces/`, `scenarios/`, `detectors/`, `alerting/`, `playbooks/`, and
  `decisions/`.
* **Update**: Moved the existing platform comparison write-up from
  `docs/comparison_report.md` into
  [`decisions/platform-comparison.md`](decisions/platform-comparison.md) as a
  `Decision Record` concept, body unchanged.
* **Update**: Documented the new pipeline-logs page
  (`dashboard/logs.html` + `dashboard/js/logs.js`) and the `log` WebSocket
  frame type it runs on — added the `log` frame shapes (per `source`:
  `generator`/`backend`/`mosquitto`) to
  [`interfaces/websocket-stream.md`](interfaces/websocket-stream.md), and
  the new files to [`components/dashboard.md`](components/dashboard.md).
  Documented the generator/backend code behind it (`rover/log/generator`
  MQTT topic, `backend.config.LOG_TOPIC_PREFIX`, `MQTTBridge._emit_raw`) in
  [`components/generator.md`](components/generator.md) and
  [`components/backend.md`](components/backend.md). Documented
  `scripts/run_all.sh` in
  [`playbooks/run-locally.md`](playbooks/run-locally.md).
* **Creation**: Documented the new simulated ROS 2 bridge (`ros2_sim/`) —
  a fake rclpy-shaped `Node`/`create_publisher`/`create_subscription`
  interface over MQTT, independent of the rest of the pipeline. Added
  [`components/ros2-bridge.md`](components/ros2-bridge.md),
  [`interfaces/ros2-bridge-topics.md`](interfaces/ros2-bridge-topics.md)
  (exact JSON shape per topic, captured live from `ros2_sim.fake_robot`),
  and [`playbooks/run-ros2-bridge.md`](playbooks/run-ros2-bridge.md).

## 2026-10-13 (continued)

* **Update**: Re-pointed `ros2_sim`'s topic set at a specific reference
  hardware stack (Leo Rover 1.9 + Arducam IMX477 HQ Camera + WidowX AI
  arm) supplied by the user. Removed `/odom`, `/battery`, `/diagnostics`
  (not in that reference list) and added `/heading_controller/cmd_vel`,
  8 `/camera/*` topics (`Image`/`CameraInfo`/`CompressedImage`, new
  dataclasses in `ros2_sim/msgs.py`, PNG-encoded via the new
  `ros2_sim/png_encode.py`), and `/arm_controller/joint_trajectory`/
  `controller_state` (`JointTrajectory`/`JointTrajectoryControllerState`,
  also new). `/joint_states` now carries wheel and arm joints in one
  combined message. Rewrote
  [`interfaces/ros2-bridge-topics.md`](interfaces/ros2-bridge-topics.md)
  with the new topic tables (by subsystem: Movement/Camera/Arm) and fresh
  live-captured samples for every topic.
* **Correction**: [`components/ros2-bridge.md`](components/ros2-bridge.md)
  previously claimed `ros2_sim` is independent of the generator/backend/
  dashboard pipeline ("the generator, backend, and dashboard never import
  it"). That's no longer true — `generator.main` and the old external
  emulator don't exist anymore, `ros2_sim.fake_robot` is this project's
  only live telemetry source, and `backend/ros2_translate.py` subscribes
  to several of its topics directly. Corrected this page,
  [`components/backend.md`](components/backend.md),
  [`components/dashboard.md`](components/dashboard.md), and the
  top-level `README.md`. Also fixed a real bug this surfaced:
  `backend/ros2_translate.py`'s `/joint_states` handling indexed into
  `position`/`velocity`/`effort` by list position (0..3), which breaks
  the moment the message also carries arm joint names — switched to
  name-based lookup (`backend.config.ROS2_WHEEL_JOINT_NAMES`/
  `ROS2_ARM_JOINT_NAMES`), added `arm/<joint>/position|effort|error`
  points, and added a regression test
  (`tests/test_ros2_translate.py`) proving wheel points are correct
  regardless of where the arm joints land in the name list.
* **Update**: Removing `/battery` removed the dashboard's only live data
  source for the Battery panel and the `battery/*` fault detectors —
  removed both (panel in `dashboard/index.html`, detector config in
  `backend/config.py`) rather than leave a dead panel. Added a Camera
  panel (live `camera/image_color/compressed` frame, broadcast as a new
  `camera_frame` WebSocket frame type documented in
  [`interfaces/websocket-stream.md`](interfaces/websocket-stream.md)) and
  an Arm panel (per-joint position/effort/error). Documented both in
  [`components/dashboard.md`](components/dashboard.md) and
  [`components/backend.md`](components/backend.md).
* **Known pre-existing drift, not addressed in this change**: `README.md`,
  [`playbooks/run-locally.md`](playbooks/run-locally.md), and
  [`components/generator.md`](components/generator.md) still describe
  `generator.main`, fault-injection scenarios, and an `/api/scenario`
  endpoint, none of which exist in the current code (`generator/` is just
  `signals.py`; `backend/app.py` has no scenario endpoint). Flagged for a
  future pass rather than fixed here, since it's unrelated to the
  ros2_sim topic/dashboard change this entry covers.
