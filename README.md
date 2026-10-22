# Rover Telemetry Dashboard / Digital Twin

A synthetic rover telemetry pipeline: an MQTT-based data generator with
selectable normal/fault scenarios, a FastAPI backend that runs statistical
fault detection and alerting, and a live static HTML dashboard.

## Components

- `generator/` — publishes synthetic rover telemetry (joints, wheels,
  battery, IMU, GPS, comms/camera heartbeats) over MQTT at a configurable
  rate. Supports runtime scenario switching (`normal`, `joint_overheat`,
  `battery_drain`, `sensor_dropout`, `comms_loss`, `wheel_slip_stall`).
- `backend/` — FastAPI app that bridges MQTT into a WebSocket stream, runs
  per-point fault detectors (threshold+hysteresis, rolling z-score,
  rate-of-change, staleness/heartbeat), manages alerts, and triggers a
  `rover/command/safe_state` MQTT message when a critical fault is active.
- `dashboard/` — a single static HTML page (Chart.js via CDN, no build
  step) that connects to the backend's WebSocket and renders live charts,
  an alert banner, and an alert log.
- `ros2_sim/` — a simulated ROS 2-to-MQTT bridge, matching the Leo Rover
  1.9 / Arducam IMX477 / WidowX AI reference topic list. No rclpy, no DDS:
  `ros2_sim.node.Node` mimics rclpy's `create_publisher`/
  `create_subscription`/`spin` shape, and `ros2_sim.msgs` has dataclasses
  matching real ROS 2 message fields (`geometry_msgs/Twist`,
  `nav_msgs/Odometry`, `sensor_msgs/{JointState,Imu,Image,CameraInfo,
  CompressedImage}`, `trajectory_msgs/JointTrajectory`,
  `control_msgs/JointTrajectoryControllerState`, `tf2_msgs/TFMessage`) for
  `/cmd_vel`, `/heading_controller/cmd_vel`, `/merged_odom`/`/wheel_odom`,
  `/joint_states` (wheels + arm, combined), `/imu/data`, `/tf`(`_static`),
  `/arm_controller/joint_trajectory`/`controller_state`, and 8 `/camera/*`
  topics. **It is not actually independent of the rest of the pipeline**:
  `ros2_sim.fake_robot` is this project's only live telemetry source, and
  `backend/ros2_translate.py` subscribes to several of its topics
  directly. See below for usage.

## Documentation

`docs/` is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
(OKF v0.2) bundle: a knowledge base of the system's components, MQTT/HTTP
interfaces, fault scenarios, detectors, alerting, playbooks, and
architecture decisions (including the Grafana Cloud / cloud IoT /
self-hosted platform comparison). Start at
[`docs/index.md`](docs/index.md).

## Running it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d                 # starts Mosquitto on localhost:1883
python -m generator.main --scenario normal --rate 4
uvicorn backend.app:app --reload     # in another terminal
open dashboard/index.html            # in another terminal/tab
```

Or start everything at once:

```bash
scripts/run_all.sh                   # [scenario] [rate_hz], default normal/4Hz
```

This brings up Mosquitto, the backend, and the generator, opens both
`dashboard/index.html` and `dashboard/logs.html`, and tails the backend +
generator logs in the foreground. Ctrl+C stops the generator and backend
(Mosquitto is left running — `docker compose down` to stop it too). If a
backend or generator is already running, it leaves them alone instead of
starting duplicates.

### Pipeline logs page

`dashboard/logs.html` shows Mosquitto/generator/backend/dashboard
side by side: each panel's live rate (`sent=…/s`, `rx=…/s -> processed ->
tx=…/s`, `displayed=…/s`) and a scrolling tail of what it's doing, fed by
`log` frames the generator and backend publish over MQTT/WebSocket once a
second (high-volume telemetry frames are counted, not logged line-by-line,
to keep it readable).

Switch scenarios either from the dashboard's dropdown or via:

```bash
curl -X POST localhost:8000/api/scenario -H 'Content-Type: application/json' -d '{"name":"joint_overheat"}'
```

Watch `rover/command/safe_state` to see the safe-state trip/clear:

```bash
python3 -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_message = lambda c,u,m: print(m.topic, m.payload.decode())
c.connect('localhost', 1883); c.subscribe('rover/command/safe_state')
c.loop_forever()
"
```

## Simulated ROS 2 bridge

`ros2_sim/` lives on its own MQTT topic namespace (`/cmd_vel`,
`/joint_states`, ...), not this project's `rover/#` tree. That's a
namespace separation, not a pipeline separation, though: the backend
explicitly subscribes to several `ros2_sim` topics
(`backend.config.ROS2_SIM_TOPICS`) and is the dashboard's only live data
source — see [`docs/components/ros2-bridge.md`](docs/components/ros2-bridge.md).

```bash
docker compose up -d                                  # needs the broker
python -m ros2_sim.fake_robot --rate 10                # the "robot" publishing
python -m ros2_sim.echo                                 # subscribes to everything, prints each message
python -m ros2_sim.echo /cmd_vel /imu/data              # or just specific topics
```

To subscribe from your own code, the whole interface is:

```python
from ros2_sim.node import Node
from ros2_sim.msgs import Imu

node = Node("my_node")
node.create_subscription(Imu, "/imu/data", lambda msg: print(msg.linear_acceleration.z))
node.spin()
```

If a real rover's ROS 2 graph ever replaces `fake_robot.py`, subscriber code
written against `ros2_sim.node.Node` doesn't change — only what's on the
other end of `/cmd_vel` etc. does.

## Tests

```bash
pytest tests/
```
