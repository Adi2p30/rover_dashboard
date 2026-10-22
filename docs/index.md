---
okf_version: "0.2"
---

# Rover Telemetry Dashboard — Knowledge Bundle

An [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
(OKF v0.2) bundle documenting this project: the synthetic rover telemetry
generator, the FastAPI backend, the static dashboard, the fault scenarios
and detectors that connect them, and the platform decisions behind the
architecture.

# Components

* [Generator](components/generator.md) - publishes synthetic rover telemetry over MQTT with selectable fault scenarios.
* [Backend](components/backend.md) - bridges MQTT to WebSocket, runs fault detection and alerting, publishes safe-state.
* [Dashboard](components/dashboard.md) - static HTML/JS page rendering live charts, an alert banner, and an alert log.
* [Broker](components/broker.md) - local Mosquitto MQTT broker started via docker-compose.
* [ROS 2 bridge (simulated)](components/ros2-bridge.md) - fake rclpy-shaped pub/sub interface over MQTT; this project's only live telemetry source, not independent of the backend/dashboard in practice.

# Interfaces

* [MQTT telemetry topics](interfaces/mqtt-telemetry.md) - the sensor topics the generator publishes each tick.
* [MQTT control topics](interfaces/mqtt-control.md) - scenario switching and safe-state announcement.
* [MQTT external-emulator topics](interfaces/mqtt-external.md) - a standalone ROS 2-style publisher emulation on the same bus.
* [HTTP API](interfaces/http-api.md) - the backend's REST endpoints.
* [WebSocket stream](interfaces/websocket-stream.md) - the `/ws` frame protocol the dashboard consumes, including the `log` frames that drive `dashboard/logs.html`.
* [ROS 2 bridge topics](interfaces/ros2-bridge-topics.md) - the simulated bridge's topics and exact message JSON shapes.

# Fault scenarios

* [normal](scenarios/normal.md) - baseline operation, no injected fault.
* [joint_overheat](scenarios/joint-overheat.md) - a joint's cooling term fails and its temperature ramps up.
* [battery_drain](scenarios/battery-drain.md) - state of charge collapses abnormally fast.
* [sensor_dropout](scenarios/sensor-dropout.md) - the IMU orientation topic stops publishing.
* [comms_loss](scenarios/comms-loss.md) - the comms heartbeat topic stops publishing.
* [wheel_slip_stall](scenarios/wheel-slip-stall.md) - a wheel stalls while commanded speed stays nominal.

# Fault detectors

* [Threshold (with hysteresis)](detectors/threshold.md) - fixed warn/fault bounds with a hysteresis band.
* [Rolling z-score](detectors/rolling-zscore.md) - EWMA mean/variance outlier detection for noisy-but-bounded signals.
* [Rate of change](detectors/rate-of-change.md) - flags sudden jumps in a signal.
* [Staleness](detectors/staleness.md) - flags a topic that has stopped publishing.

# Alerting

* [Alert manager](alerting/alert-manager.md) - tracks active alerts and derives safe-state.
* [Safe-state publisher](alerting/safe-state.md) - publishes the retained safe-state MQTT message.

# Playbooks

* [Run locally](playbooks/run-locally.md) - stand up the full stack on a dev machine.
* [Switch scenario](playbooks/switch-scenario.md) - change the active fault scenario at runtime.
* [Run tests](playbooks/run-tests.md) - run the pytest suite.
* [Run the simulated ROS 2 bridge](playbooks/run-ros2-bridge.md) - start the fake rover publisher and a subscriber against it.

# Decisions

* [Platform comparison](decisions/platform-comparison.md) - why this project is self-hosted and MQTT-native rather than on Grafana Cloud or a cloud IoT platform.
