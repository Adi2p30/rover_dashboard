---
type: Playbook
title: Run locally
description: Stand up the broker, generator, backend, and dashboard on a local dev machine.
tags: [playbook, setup]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T18:30:41Z }
---

# Steps

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d                 # starts Mosquitto on localhost:1883
python -m generator.main --scenario normal --rate 4
uvicorn backend.app:app --reload     # in another terminal
open dashboard/index.html            # in another terminal/tab
open dashboard/logs.html             # pipeline-logs page: Mosquitto/Generator/Backend/Dashboard side by side
```

Or start everything at once with [`scripts/run_all.sh`](../../scripts/run_all.sh)
(`./scripts/run_all.sh [scenario] [rate_hz]`) — brings up Mosquitto, the
backend, and the generator, opens both dashboard pages, and tails the
backend + generator logs in the foreground; Ctrl+C stops the generator and
backend (Mosquitto is left running). It won't start a duplicate backend or
generator if one is already running.

Watch the safe-state trip/clear directly on the broker:

```bash
python3 -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_message = lambda c,u,m: print(m.topic, m.payload.decode())
c.connect('localhost', 1883); c.subscribe('rover/command/safe_state')
c.loop_forever()
"
```

# Related

* [Broker](../components/broker.md)
* [Generator](../components/generator.md)
* [Backend](../components/backend.md)
* [Dashboard](../components/dashboard.md)
