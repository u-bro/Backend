from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

from app.services.chat_service import chat_service, MessageType, ModerationResult
from app.db import async_session_maker
from app.services.websocket_manager import manager
from app.crud.chat_message import chat_message_crud

logger = logging.getLogger(__name__)

router = APIRouter()

class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    message_type: str = Field(default="text")
    receiver_id: Optional[int] = None
    attachments: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseModel):
    id: int
    ride_id: int
    sender_id: int
    text: str
    message_type: str
    is_moderated: bool
    created_at: datetime
    moderation_note: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    ride_id: int
    messages: List[Dict[str, Any]]
    count: int
    has_more: bool


class ChatMessageOut(BaseModel):
    id: int
    ride_id: Optional[int]
    sender_id: Optional[int]
    text: Optional[str]
    message_type: Optional[str]
    is_moderated: bool
    created_at: Optional[datetime]
    edited_at: Optional[datetime]
    deleted: bool = False

    class Config:
        from_attributes = True


@router.websocket("/chat/ws/{ride_id}")
async def chat_websocket(
    websocket: WebSocket,
    ride_id: int,
    user_id: int = Query(..., description="ID пользователя"),
    token: Optional[str] = Query(None, description="Auth token"),
):
    await manager.connect(websocket, user_id)
    manager.join_ride(ride_id, user_id)
    await manager.send_to_ride(ride_id, {
        "type": "user_joined",
        "ride_id": ride_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude_user_id=user_id)
    
    await websocket.send_json({
        "type": "connected",
        "ride_id": ride_id,
        "user_id": user_id,
        "message": "Connected to chat"
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            await handle_chat_message(websocket, ride_id, user_id, data)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        manager.leave_ride(ride_id, user_id)

        await manager.send_to_ride(ride_id, {
            "type": "user_left",
            "ride_id": ride_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user_id} disconnected from chat {ride_id}")
    
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
        manager.leave_ride(ride_id, user_id)


async def handle_chat_message(
    websocket: WebSocket, 
    ride_id: int, 
    user_id: int, 
    data: dict
) -> None:
    
    msg_type = data.get("type", "message")
    
    if msg_type == "ping":
        await websocket.send_json({"type": "pong"})
        return
    
    if msg_type == "typing":
        await manager.send_to_ride(ride_id, {
            "type": "user_typing",
            "ride_id": ride_id,
            "user_id": user_id,
        }, exclude_user_id=user_id)
        return
    
    if msg_type == "message":
        logger.info("WS received raw from user %s in ride %s: %s", user_id, ride_id, data)
        try:
            await websocket.send_json({"type": "echo", "message": data})
        except Exception:
            pass

        text = data.get("text", "").strip()
        message_type = data.get("message_type", MessageType.TEXT)
        
        if not text:
            await websocket.send_json({
                "type": "error",
                "code": "empty_message",
                "message": "Message text is required"
            })
            return
        
        allowed, error = chat_service.check_rate_limit(user_id)
        if not allowed:
            await websocket.send_json({
                "type": "error",
                "code": "rate_limit",
                "message": error
            })
            return
        
        moderation = chat_service.moderate_message(text)
        
        if not moderation.passed:
            await websocket.send_json({
                "type": "error",
                "code": "moderation_failed",
                "message": moderation.reason
            })
            return
        
        try:
            async with async_session_maker() as session:
                message = await chat_service.save_message(
                    session=session,
                    ride_id=ride_id,
                    sender_id=user_id,
                    text=moderation.filtered,
                    message_type=message_type,
                    is_moderated=True,
                )
                await session.commit()

            message_payload = {
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
            }

            await manager.send_to_ride(ride_id, message_payload)
            logger.info(f"Chat message saved and broadcast for ride {ride_id} from user {user_id} (id={message.id})")
        except Exception as exc:
            logger.error(f"Failed to save/broadcast chat message: {exc}")
            await websocket.send_json({
                "type": "error",
                "code": "save_failed",
                "message": "Failed to save message",
            })
            return


@router.get("/chat/{ride_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    request: Request,
    ride_id: int,
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[int] = Query(None, description="Для пагинации - ID сообщения"),
):

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


@router.post("/chat/{ride_id}/send", response_model=SendMessageResponse)
async def send_message(
    request: Request,
    ride_id: int,
    body: SendMessageRequest,
    sender_id: int = Query(..., description="ID отправителя"),
):
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
    
    await session.commit()
    await manager.send_to_ride(ride_id, {
        "type": "new_message",
        "message": {
            "id": message.id,
            "ride_id": ride_id,
            "sender_id": sender_id,
            "text": message.text,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
    })
    
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


@router.delete("/chat/{ride_id}/message/{message_id}")
async def delete_message(
    request: Request,
    ride_id: int,
    message_id: int,
    user_id: int = Query(..., description="ID пользователя"),
):
    session = request.state.session
    
    deleted = await chat_service.soft_delete_message(
        session=session,
        message_id=message_id,
        user_id=user_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=404, 
            detail="Message not found or you don't have permission"
        )
    
    await session.commit()
    
    await manager.send_to_ride(ride_id, {
        "type": "message_deleted",
        "message_id": message_id,
        "deleted_by": user_id,
    })
    
    return {"status": "deleted", "message_id": message_id}


@router.put("/chat/{ride_id}/message/{message_id}")
async def edit_message(
    request: Request,
    ride_id: int,
    message_id: int,
    body: SendMessageRequest,
    user_id: int = Query(..., description="ID пользователя"),
):
    session = request.state.session
    
    message = await chat_service.edit_message(
        session=session,
        message_id=message_id,
        user_id=user_id,
        new_text=body.text,
    )
    
    if not message:
        raise HTTPException(
            status_code=404, 
            detail="Message not found or you don't have permission"
        )
    
    await session.commit()
    
    await manager.send_to_ride(ride_id, {
        "type": "message_edited",
        "message": {
            "id": message.id,
            "text": message.text,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        }
    })
    
    return {
        "status": "edited",
        "message": {
            "id": message.id,
            "text": message.text,
            "edited_at": message.edited_at,
        }
    }


@router.get("/chat/stats")
async def get_chat_stats():
    return chat_service.get_stats()


chat_router = router
