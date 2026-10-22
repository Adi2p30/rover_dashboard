"""FastAPI app: REST control endpoints + a /ws stream of telemetry and alerts."""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.mqtt_bridge import MQTTBridge

sys.stdout.reconfigure(line_buffering=True)  # so pipeline logs show up live even when piped/redirected

_clients: set[WebSocket] = set()


async def broadcast(frame: dict) -> None:
    stale = []
    for ws in _clients:
        try:
            await ws.send_json(frame)
        except Exception:
            stale.append(ws)
    for ws in stale:
        _clients.discard(ws)


bridge = MQTTBridge(broadcast_fn=broadcast)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bridge.start()
    yield
    await bridge.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/state")
async def state():
    return bridge.state_store.snapshot()


@app.get("/api/alerts")
async def alerts():
    return bridge.alert_manager.snapshot()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)
    print(f"[backend] dashboard client connected (total={len(_clients)})")
    try:
        await websocket.send_json({"type": "snapshot", "state": bridge.state_store.snapshot(), "alerts": bridge.alert_manager.snapshot()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(websocket)
        print(f"[backend] dashboard client disconnected (total={len(_clients)})")
