---
type: API Endpoint
title: HTTP API
description: The FastAPI backend's REST endpoints for health, state, alert, and scenario control.
resource: ../../backend/app.py
tags: [api, rest, fastapi]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Endpoints

| Method | Path | Response / body |
|--------|------|------------------|
| GET | `/api/health` | `{"status": "ok"}` |
| GET | `/api/state` | Latest payload per point id — `StateStore.snapshot()`. |
| GET | `/api/alerts` | `{"active_alerts": [...], "log": [...], "safe_state_active": bool}` — `AlertManager.snapshot()`. |
| POST | `/api/scenario` | Body `{"name": "<scenario>"}`. Publishes `rover/command/set_scenario`; responds `{"ok": true, "name": "<scenario>"}` unconditionally — there's no server-side validation of `name`, and the generator's `ScenarioRunner.set_scenario()` silently ignores a name that isn't a known scenario. |

CORS is wide open (`allow_origins=["*"]`) since the dashboard is a static
file opened directly in a browser, not served from the same origin as the
backend.

# Related

* [WebSocket stream](websocket-stream.md)
* [Switch scenario](../playbooks/switch-scenario.md)
* [Dashboard](../components/dashboard.md)
