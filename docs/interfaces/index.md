# Interfaces

* [MQTT telemetry topics](mqtt-telemetry.md) - the sensor topics the generator publishes each tick.
* [MQTT control topics](mqtt-control.md) - scenario switching and safe-state announcement.
* [MQTT external-emulator topics](mqtt-external.md) - a standalone ROS 2-style publisher emulation on the same bus.
* [HTTP API](http-api.md) - the backend's REST endpoints.
* [WebSocket stream](websocket-stream.md) - the `/ws` frame protocol the dashboard consumes, including the `log` frames that drive `dashboard/logs.html`.
* [ROS 2 bridge topics](ros2-bridge-topics.md) - the simulated bridge's topics and exact message JSON shapes.
