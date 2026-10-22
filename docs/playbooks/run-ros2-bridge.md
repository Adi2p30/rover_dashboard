---
type: Playbook
title: Run the simulated ROS 2 bridge
description: Start the fake rover publisher and a subscriber against it.
tags: [playbook, ros2, simulation]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Steps

Needs only the broker to run on its own. In practice, `ros2_sim.fake_robot`
is this project's only live telemetry source, so the backend (and
therefore the dashboard) needs it running too — see
[Run locally](run-locally.md).

```bash
docker compose up -d                         # starts Mosquitto on localhost:1883
python -m ros2_sim.fake_robot --rate 10      # the "robot" publishing
python -m ros2_sim.echo                      # in another terminal: subscribes to everything
python -m ros2_sim.echo /cmd_vel /imu/data   # or just specific topics
```

To subscribe from your own code, the whole interface is:

```python
from ros2_sim.node import Node
from ros2_sim.msgs import Imu

node = Node("my_node")
node.create_subscription(Imu, "/imu/data", lambda msg: print(msg.linear_acceleration.z))
node.spin()
```

If a real rover's ROS 2 graph ever replaces `fake_robot.py`, subscriber
code written against `ros2_sim.node.Node` doesn't change — only what's on
the other end of `/cmd_vel` etc. does.

# Related

* [ROS 2 bridge (simulated)](../components/ros2-bridge.md)
* [ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md)
* [Broker](../components/broker.md)
