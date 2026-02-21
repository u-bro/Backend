from typing import Any, Dict, Optional
from fastapi import HTTPException, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.base import BaseRouter
from app.schemas.chat_message import ChatHistoryResponse, SendMessageRequest, ChatMessageSchema, ChatMessageHistory, ChatRidesDelete, UserChatReceiver
from app.services.chat_service import chat_service
from app.crud import ride_crud, user_crud
from app.backend.deps import get_current_user_id
from app.services.websocket_manager import manager
from app.models.chat_message import ChatMessage
from datetime import datetime, timezone


class ChatHttpRouter(BaseRouter):
    def __init__(self, model_crud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/history", self.get_chat_history, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/send", self.send_message, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/message/{{message_id}}", self.delete_message, methods=["DELETE"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/message/{{message_id}}", self.edit_message, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/message/{{message_id}}/read", self.mark_message_read, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/read", self.mark_ride_messages_read, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me", self.get_my_chats, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/stats", self.get_chat_stats, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me/delete", self.delete_messages_by_ride_ids, methods=["POST"], status_code=200)

    async def get_my_chats(self, request: Request, page: int = 1, page_size: int = 10, user_id: int = Depends(get_current_user_id)) -> list[ChatMessageHistory]:
        session = request.state.session
        return await chat_service.get_my_chats(session=session, user_id=user_id, page=page, page_size=page_size)

    async def get_chat_history(self, request: Request, ride_id: int, page_size: int = Query(50, ge=1, le=100), page: int = Query(1, ge=1), user_id = Depends(get_current_user_id)) -> ChatHistoryResponse:
        session = request.state.session
        ride, driver_profile = await self._check_permission(session, ride_id, user_id)

        messages = await chat_service.get_chat_history(session=session, ride_id=ride_id, page_size=page_size, page=page, current_user_id=user_id)
        if user_id == ride.client_id:
            receiver = UserChatReceiver(first_name=driver_profile.first_name, last_name=driver_profile.last_name, middle_name=driver_profile.middle_name, photo_url=driver_profile.photo_url)
        else:
            client = await user_crud.get_by_id(session=session, id=ride.client_id)
            receiver = UserChatReceiver(first_name=client.first_name, last_name=client.last_name, middle_name=client.middle_name, photo_url=client.photo_url)

        return ChatHistoryResponse(ride_id=ride_id, messages=[m.model_dump() for m in messages], count=len(messages), receiver=receiver)

    async def send_message(self, request: Request, ride_id: int, body: SendMessageRequest, sender_id: int = Depends(get_current_user_id)) -> ChatMessageSchema:
        session = request.state.session
        await self._check_permission(session, ride_id, sender_id)
        allowed, error = chat_service.check_rate_limit(sender_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=error)

        message = await chat_service.save_message(session, ChatMessage(ride_id=ride_id, sender_id=sender_id, text=body.text, message_type=body.message_type, attachments=body.attachments, is_moderated=True, created_at=datetime.now(timezone.utc)))
        await manager.send_to_ride(session, ride_id, {"type": "new_message", "message": {"id": message.id, "ride_id": ride_id, "sender_id": sender_id, "text": message.text, "message_type": message.message_type, "is_moderated": message.is_moderated, "is_read": message.is_read, "created_at": message.created_at.isoformat() if message.created_at else None}})
        return message

    async def delete_message(self, request: Request, ride_id: int, message_id: int, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        await self._check_permission(session, ride_id, user_id)
        is_deleted = await chat_service.soft_delete_message(session=session, message_id=message_id, user_id=user_id)
        if is_deleted:
            await manager.send_to_ride(session, ride_id, {"type": "message_deleted", "message_id": message_id, "deleted_by": user_id})
        return {"is_deleted": is_deleted, "message_id": message_id}

    async def edit_message(self, request: Request, ride_id: int, message_id: int, body: SendMessageRequest, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        await self._check_permission(session, ride_id, user_id)
        message = await chat_service.edit_message(session=session, message_id=message_id, new_text=body.text)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

        await manager.send_to_ride(session, ride_id, {"type": "message_edited", "message": {"id": message.id, "text": message.text, "edited_at": message.edited_at.isoformat() if message.edited_at else None}})
        return {"status": "edited", "message": {"id": message.id, "text": message.text, "edited_at": message.edited_at}}

    async def mark_message_read(self, request: Request, ride_id: int, message_id: int, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        await self._check_permission(session, ride_id, user_id)        
        updated = await chat_service.mark_message_read(session=session, ride_id=ride_id, message_id=message_id, user_id=user_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Message not found")

        await manager.send_to_ride(session, ride_id, {"type": "message_read", "ride_id": ride_id, "message_id": updated.id, "read_by": user_id, "is_read": True}, exclude_user_id=user_id)
        return {"status": "ok", "message_id": updated.id, "is_read": True}

    async def mark_ride_messages_read(self, request: Request, ride_id: int, up_to_id: Optional[int] = Query(None, description="mark messages with id <= up_to_id as read"), user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        await self._check_permission(session, ride_id, user_id)
        updated_count = await chat_service.mark_ride_messages_read(session=session, ride_id=ride_id, user_id=user_id, up_to_id=up_to_id)
        await manager.send_to_ride(session, ride_id, {"type": "ride_messages_read", "ride_id": ride_id, "read_by": user_id, "up_to_id": up_to_id, "updated": updated_count}, exclude_user_id=user_id)
        return {"status": "ok", "ride_id": ride_id, "up_to_id": up_to_id, "updated": updated_count}

    async def get_chat_stats(self) -> Dict[str, Any]:
        return chat_service.get_stats()

    async def delete_messages_by_ride_ids(self, request: Request, body: ChatRidesDelete, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        my_rides = await ride_crud.get_by_client_id(session=session, client_id=user_id)
        my_rides_ids = [ride.id for ride in my_rides]
        if not set(body.ride_ids).issubset(my_rides_ids):
            raise HTTPException(status_code=403, detail="Forbidden")
        deleted = await chat_service.delete_messages_by_ride_ids(session=session, ride_ids=body.ride_ids)
        return {"deleted": deleted}

    async def _check_permission(self, session: AsyncSession, ride_id: int, user_id: int):
        ride = await ride_crud.get_by_id_with_driver_profile(session, ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        driver_profile = ride.driver_profile
        if user_id != ride.client_id and user_id != getattr(driver_profile, 'user_id', None):
            raise HTTPException(status_code=403, detail="Forbidden")
        
        return ride, driver_profile

chat_http_router = ChatHttpRouter(chat_service, "/chat").router
