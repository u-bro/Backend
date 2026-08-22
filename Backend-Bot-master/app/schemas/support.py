from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseSchema


class MaxLinkResponse(BaseModel):
    type: str = "max"
    url: str


class MaxWebhookRequest(BaseModel):
    # Kept generic because MAX's official event schema is not available to this service.
    event: str | None = None
    type: str | None = None
    chat_id: int | str | None = None
    user_id: int | str | None = None
    message_id: int | str | None = None
    text: str | None = None
    message: dict | None = None


class SupportMessageResponse(BaseSchema):
    id: int
    sender_type: str
    user_id: int | None = None
    text: str
    external_message_id: str | None = None
    created_at: datetime


class SupportConversationSummary(BaseSchema):
    id: int
    user_id: int | None = None
    max_user_id: int | None = None
    max_chat_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    latest_message: SupportMessageResponse | None = None


class SupportConversationDetail(SupportConversationSummary):
    messages: list[SupportMessageResponse] = Field(default_factory=list)


class SupportMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1_000_000)


class SupportCloseResponse(BaseModel):
    id: int
    status: str
