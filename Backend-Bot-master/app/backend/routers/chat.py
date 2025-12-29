from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import HTTPException, Query, Request, WebSocket, Depends, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.db import async_session_maker
from app.logger import logger
from app.schemas.chat_message import ChatHistoryResponse, SendMessageRequest, SendMessageResponse
from app.services.chat_service import MessageType, chat_service
from app.services.websocket_manager import manager
from app.backend.deps import get_current_user_id, get_current_user_id_ws
from starlette.status import WS_1008_POLICY_VIOLATION


class ChatWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/chat/ws/{ride_id}", self.websocket_endpoint)

        self.router.add_api_route("/chat/{ride_id}/history", self.get_chat_history, methods=["GET"], status_code=200)
        self.router.add_api_route("/chat/{ride_id}/send", self.send_message, methods=["POST"], status_code=200)
        self.router.add_api_route("/chat/{ride_id}/message/{message_id}", self.delete_message, methods=["DELETE"], status_code=200)
        self.router.add_api_route("/chat/{ride_id}/message/{message_id}", self.edit_message, methods=["PUT"], status_code=200)
        self.router.add_api_route("/chat/stats", self.get_chat_stats, methods=["GET"], status_code=200)

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
                "timestamp": datetime.utcnow().isoformat(),
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
                "timestamp": datetime.utcnow().isoformat(),
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

    async def get_chat_history(self, request: Request, ride_id: int, limit: int = Query(50, ge=1, le=100), before_id: Optional[int] = Query(None, description="message id")) -> ChatHistoryResponse:
        session = request.state.session

        messages = await chat_service.get_chat_history(
            session=session,
            ride_id=ride_id,
            limit=limit + 1,
            before_id=before_id,
        )

        has_more = len(messages) > limit
        if has_more:
            messages = messages[1:]

        return ChatHistoryResponse(
            ride_id=ride_id,
            messages=[
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "text": m.text,
                    "message_type": m.message_type,
                    "is_moderated": m.is_moderated,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "edited_at": m.edited_at.isoformat() if m.edited_at else None,
                    "deleted": m.deleted_at is not None,
                }
                for m in messages
            ],
            count=len(messages),
            has_more=has_more,
        )

    async def send_message(self, request: Request, ride_id: int, body: SendMessageRequest, sender_id: int = Depends(get_current_user_id)) -> SendMessageResponse:
        session = request.state.session
        allowed, error = chat_service.check_rate_limit(sender_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=error)
        moderation = chat_service.moderate_message(body.text)

        if not moderation.passed:
            raise HTTPException(status_code=400, detail=moderation.reason)

        message = await chat_service.save_message(
            session=session,
            ride_id=ride_id,
            sender_id=sender_id,
            text=moderation.filtered,
            message_type=body.message_type,
            receiver_id=body.receiver_id,
            attachments=body.attachments,
            is_moderated=True,
        )

        await manager.send_to_ride(
            ride_id,
            {
                "type": "new_message",
                "message": {
                    "id": message.id,
                    "ride_id": ride_id,
                    "sender_id": sender_id,
                    "text": message.text,
                    "message_type": message.message_type,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                },
            },
        )

        return SendMessageResponse(
            id=message.id,
            ride_id=ride_id,
            sender_id=sender_id,
            text=message.text,
            message_type=message.message_type,
            is_moderated=message.is_moderated,
            created_at=message.created_at,
            moderation_note="Censored" if moderation.original != moderation.filtered else None,
        )

    async def delete_message(self, request: Request, ride_id: int, message_id: int, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session

        deleted = await chat_service.soft_delete_message(
            session=session,
            message_id=message_id,
            user_id=user_id,
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

        await manager.send_to_ride(
            ride_id,
            {
                "type": "message_deleted",
                "message_id": message_id,
                "deleted_by": user_id,
            },
        )

        return {"status": "deleted", "message_id": message_id}

    async def edit_message(self, request: Request, ride_id: int, message_id: int, body: SendMessageRequest, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session

        message = await chat_service.edit_message(
            session=session,
            message_id=message_id,
            user_id=user_id,
            new_text=body.text,
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

        await manager.send_to_ride(
            ride_id,
            {
                "type": "message_edited",
                "message": {
                    "id": message.id,
                    "text": message.text,
                    "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                },
            },
        )

        return {
            "status": "edited",
            "message": {
                "id": message.id,
                "text": message.text,
                "edited_at": message.edited_at,
            },
        }

    async def get_chat_stats(self) -> Dict[str, Any]:
        return chat_service.get_stats()


chat_router = ChatWebsocketRouter().router
