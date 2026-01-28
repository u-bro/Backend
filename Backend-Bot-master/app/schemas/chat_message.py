from typing import Any, Dict, List, Optional
from .base import BaseSchema
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageSchema(BaseSchema):
    id: int
    ride_id: Optional[int] = None
    text: Optional[str] = None
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    message_type: Optional[str] = None
    attachments: Optional[dict[str, Any]] = None
    is_moderated: bool
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    message_type: str = Field(default="text")
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
    user_ids: List[int]
    count: int
    has_more: bool


class ChatMessageHistory(BaseModel):
    ride_id: int
    messages: List[ChatMessageSchema]
