"""WebSocket stream: market bars and insights."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from quantedge_backend.observability.metrics import inc

log = structlog.get_logger("websocket")

router = APIRouter(prefix="/v1", tags=["stream"])


class ConnectionManager:
    """Fan-out to subscribed channels (e.g. ``market:ES:5m``, ``insights:ES``)."""

    def __init__(self) -> None:
        self._channel_clients: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def register(self, websocket: WebSocket, channels: list[str]) -> None:
        async with self._lock:
            for ch in channels:
                self._channel_clients.setdefault(ch, set()).add(websocket)

    async def unregister_all(self, websocket: WebSocket) -> None:
        async with self._lock:
            for subs in self._channel_clients.values():
                subs.discard(websocket)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._channel_clients.get(channel, set()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                if ws.client_state != WebSocketState.CONNECTED:
                    dead.append(ws)
                    continue
                await ws.send_json(message)
                inc("quantedge_ws_messages_sent_total")
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    for subs in self._channel_clients.values():
                        subs.discard(ws)


@router.websocket("/ws")
async def stream_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    manager: ConnectionManager = websocket.app.state.ws_manager
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "code": "bad_json", "message": "invalid JSON"},
                )
                continue
            mtype = msg.get("type")
            if mtype == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if mtype == "subscribe":
                chans = msg.get("channels") or []
                if isinstance(chans, list):
                    await manager.register(websocket, [str(c) for c in chans])
                await websocket.send_json({"type": "subscribed", "channels": chans})
                continue
            if mtype == "unsubscribe":
                await manager.unregister_all(websocket)
                await websocket.send_json({"type": "unsubscribed"})
                continue
            await websocket.send_json(
                {"type": "error", "code": "unknown_type", "message": str(mtype)},
            )
    except WebSocketDisconnect:
        await manager.unregister_all(websocket)
        log.info("ws_disconnected")
    except Exception as e:  # noqa: BLE001
        log.warning("ws_error", error=str(e))
        await manager.unregister_all(websocket)
