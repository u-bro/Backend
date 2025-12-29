from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from app.logger import logger

MessageHandler = Callable[[WebSocket, Dict[str, Any], Dict[str, Any]], Awaitable[None]]


class BaseWebsocketRouter:
    def __init__(self) -> None:
        self.router = APIRouter()
        self._handlers: Dict[str, MessageHandler] = {}
        self.setup_routes()

    def setup_routes(self) -> None:
        raise NotImplementedError

    def register_handler(self, msg_type: str, handler: MessageHandler) -> None:
        self._handlers[msg_type] = handler

    async def run(self, websocket: WebSocket, **context: Any) -> None:
        await self.on_connect(websocket, **context)

        try:
            while True:
                data = await websocket.receive_json()
                await self.dispatch_message(websocket, data, **context)
        except WebSocketDisconnect:
            await self.on_disconnect(websocket, **context)
        except Exception as exc:
            logger.error(f"WebSocket error: {exc}")
            await self.on_error(websocket, exc, **context)
            await self.on_disconnect(websocket, **context)

    async def dispatch_message(self, websocket: WebSocket, data: Dict[str, Any], **context: Any) -> None:
        message_type = data.get("type")
        handler = self._handlers.get(message_type)

        if not handler:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                }
            )
            return

        await handler(websocket, data, context)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        return None

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        return None

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        return None
