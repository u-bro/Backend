from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import WebSocket, Depends, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.db import async_session_maker
from app.logger import logger
from app.services.chat_service import MessageType, chat_service
from app.services.websocket_manager import manager
from app.backend.deps import get_current_user_id_ws
from starlette.status import WS_1008_POLICY_VIOLATION


class ChatWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/chat/ws/{ride_id}", self.websocket_endpoint)

    def __init__(self) -> None:
        super().__init__()
        self.register_handler("ping", self.handle_ping)
        self.register_handler("typing", self.handle_typing)
        self.register_handler("message", self.handle_message)

    async def dispatch_message(self, websocket: WebSocket, data: Dict[str, Any], **context: Any) -> None:
        normalized = dict(data)
        normalized.setdefault("type", "message")
        await super().dispatch_message(websocket, normalized, **context)

    async def websocket_endpoint(self, websocket: WebSocket, ride_id: int, user_id: int = Depends(get_current_user_id_ws)) -> None:
        async with async_session_maker() as session:
            await self.run(websocket, ride_id=ride_id, user_id=user_id, session=session)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        ride_id = int(context["ride_id"])
        user_id = int(context["user_id"])
        session: AsyncSession = context["session"]

        is_ride_participant = await chat_service.verify_ride_user(session=session, ride_id=ride_id, user_id=user_id)
        if not is_ride_participant:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason=f"Not a participant of ride {ride_id}")

        await manager.connect(websocket, user_id)
        manager.join_ride(ride_id, user_id)

        await manager.send_to_ride(
            ride_id,
            {
                "type": "user_joined",
                "ride_id": ride_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            exclude_user_id=user_id,
        )

        await websocket.send_json(
            {
                "type": "connected",
                "ride_id": ride_id,
                "user_id": user_id,
                "message": "Connected to chat",
            }
        )

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        ride_id = int(context["ride_id"])
        user_id = int(context["user_id"])

        manager.disconnect(websocket, user_id)
        manager.leave_ride(ride_id, user_id)

        await manager.send_to_ride(
            ride_id,
            {
                "type": "user_left",
                "ride_id": ride_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            exclude_user_id=user_id,
        )

        logger.info(f"User {user_id} disconnected from chat {ride_id}")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"Chat WebSocket error for user {user_id}: {exc}")

        session: AsyncSession | None = context.get("session")
        if session is not None:
            await session.rollback()

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

    async def handle_typing(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        ride_id = int(context["ride_id"])
        user_id = int(context["user_id"])

        await manager.send_to_ride(
            ride_id,
            {
                "type": "user_typing",
                "ride_id": ride_id,
                "user_id": user_id,
            },
            exclude_user_id=user_id,
        )

    async def handle_message(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        ride_id = int(context["ride_id"])
        user_id = int(context["user_id"])
        session: AsyncSession = context["session"]

        text = (data.get("text") or "").strip()
        message_type = data.get("message_type", MessageType.TEXT)

        if not text:
            await websocket.send_json({"type": "error", "code": "empty_message", "message": "Message text is required"})
            return

        allowed, error = chat_service.check_rate_limit(user_id)
        if not allowed:
            await websocket.send_json({"type": "error", "code": "rate_limit", "message": error})
            return

        moderation = chat_service.moderate_message(text)

        if not moderation.passed:
            await websocket.send_json({"type": "error", "code": "moderation_failed", "message": moderation.reason})
            return

        message = await chat_service.save_message(
            session=session,
            ride_id=ride_id,
            sender_id=user_id,
            text=moderation.filtered,
            message_type=message_type,
            receiver_id=data.get("receiver_id"),
            attachments=data.get("attachments"),
            is_moderated=True,
        )

        await manager.send_to_ride(
            ride_id,
            {
                "type": "new_message",
                "message": {
                    "id": message.id,
                    "ride_id": ride_id,
                    "sender_id": user_id,
                    "text": message.text,
                    "message_type": message.message_type,
                    "is_moderated": message.is_moderated,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                    "censored": moderation.original != moderation.filtered,
                },
            },
        )

        logger.info(f"Chat message in ride {ride_id} from user {user_id}")

chat_ws_router = ChatWebsocketRouter().router
