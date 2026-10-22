# Components

* [Generator](generator.md) - publishes synthetic rover telemetry over MQTT with selectable fault scenarios.
* [Backend](backend.md) - bridges MQTT to WebSocket, runs fault detection and alerting, publishes safe-state.
* [Dashboard](dashboard.md) - static HTML/JS page rendering live charts, an alert banner, and an alert log.
* [Broker](broker.md) - local Mosquitto MQTT broker started via docker-compose.
* [ROS 2 bridge (simulated)](ros2-bridge.md) - fake rclpy-shaped pub/sub interface over MQTT, independent of the pipeline above.
