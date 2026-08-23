from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .base import BaseSchema


class MaxLinkResponse(BaseModel):
    type: str = "max"
    url: str
    expires_at: datetime | None = None
    source: str


class LandingSupportLinkCreate(BaseModel):
    campaign: str | None = Field(None, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")


class SupportAttachmentResponse(BaseSchema):
    id: int
    attachment_type: str
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    provider_url: str | None = None
    provider_metadata: dict[str, Any] | None = None


class SupportMessageResponse(BaseSchema):
    id: int
    sender_type: str
    user_id: int | None = None
    text: str | None = None
    external_message_id: str | None = None
    message_type: str = "TEXT"
    delivery_status: str = "RECEIVED"
    delivery_error: str | None = None
    operator_name: str | None = None
    attachments: list[SupportAttachmentResponse] = Field(default_factory=list)
    created_at: datetime


class SupportConversationSummary(BaseSchema):
    id: int
    user_id: int | None = None
    max_user_id: int | None = None
    max_chat_id: int
    status: str
    source: str = "DIRECT"
    created_at: datetime
    updated_at: datetime
    last_inbound_at: datetime | None = None
    last_outbound_at: datetime | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    has_unread: bool = False
    unread_count: int = 0
    display_name: str | None = None
    phone: str | None = None
    latest_message: SupportMessageResponse | None = None


class SupportConversationDetail(SupportConversationSummary):
    messages: list[SupportMessageResponse] = Field(default_factory=list)


class SupportConversationList(BaseModel):
    items: list[SupportConversationSummary]
    next_cursor: int | None = None


class SupportMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    idempotency_key: str = Field(..., min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")


class SupportReadCreate(BaseModel):
    up_to_message_id: int = Field(..., ge=1)


class SupportReadResponse(BaseModel):
    id: int
    last_read_message_id: int | None
    unread_count: int


class SupportUnreadCount(BaseModel):
    unread_messages: int
    unread_conversations: int


class SupportCloseResponse(BaseModel):
    id: int
    status: str
