---
type: Component
title: Dashboard
description: A single static HTML page (Chart.js via CDN, no build step) that connects to the backend's WebSocket and renders live charts, an alert banner, and an alert log.
resource: ../../dashboard/
tags: [dashboard, frontend]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T20:10:00Z }
---

# Overview

A static page with no build step or framework. It opens a WebSocket
connection to the backend, reconnecting with exponential backoff on
disconnect, and renders every incoming frame into charts, an alert banner,
and an alert log. Panels: Joints, Wheels, IMU, Comms, Camera, and Arm — see
[ROS 2 bridge topics](../interfaces/ros2-bridge-topics.md) for where
Camera's frame and Arm's per-joint position/effort/error come from (the
`camera_frame` WebSocket frame and `arm/*` points, respectively). There is
no Battery panel: `/battery` isn't a topic in this project's current
reference topic list (Leo Rover 1.9 + Arducam IMX477 + WidowX AI), so
nothing publishes battery data for it to show.

A second page, `logs.html`, shares the same `ws_client.js` connection but
renders pipeline visibility instead of telemetry: four side-by-side panels
(Mosquitto, Generator, Backend, Dashboard) each showing a live rate line
and a scrolling tail, fed by the `log` WebSocket frames described in
[WebSocket stream](../interfaces/websocket-stream.md). High-volume
`telemetry` frames are counted into the Dashboard panel's rate rather than
logged line-by-line, to keep the tail readable.

# Files

| File | Role |
|------|------|
| [`index.html`](../../dashboard/index.html) | Page structure: chart canvases, alert banner, alert log, scenario dropdown. |
| [`js/ws_client.js`](../../dashboard/js/ws_client.js) | Opens the `/ws` connection, reconnect/backoff logic, and `setScenario()` which POSTs to `/api/scenario`. Shared by both `index.html` and `logs.html`. |
| [`js/charts.js`](../../dashboard/js/charts.js) | Chart.js wiring: renders `telemetry` frames into live charts (Joints/Wheels/IMU/Arm). `updateCameraFrame()` handles the separate `camera_frame` frame type by setting an `<img>`'s `src` to a `data:image/<format>;base64,...` URI directly -- not a Chart.js chart, since it's an image, not a time series. |
| [`js/alerts.js`](../../dashboard/js/alerts.js) | Renders `alert` frames into the banner and log. |
| [`css/style.css`](../../dashboard/css/style.css) | Styling, including the normal/warning/fault color coding. |
| [`logs.html`](../../dashboard/logs.html) | The pipeline-logs page: four status panels (Mosquitto/Generator/Backend/Dashboard). |
| [`js/logs.js`](../../dashboard/js/logs.js) | Routes every `log`/`detector`/`alert`/`snapshot` frame to the right panel's stats line and scrolling tail; computes the Dashboard panel's own `displayed=.../s` rate from all incoming frames; derives Mosquitto's live/stale dot from the backend's periodic `mqtt_connected` field. |
| [`css/logs.css`](../../dashboard/css/logs.css) | Four-column grid, terminal-style scrolling tail, live/stale status dot. |

# Related

* [WebSocket stream](../interfaces/websocket-stream.md)
* [HTTP API](../interfaces/http-api.md)
* [Switch scenario](../playbooks/switch-scenario.md)
