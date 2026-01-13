from typing import Any, Dict, Optional

from pydantic import Field

from .base import BaseSchema


class PushSendToTokenRequest(BaseSchema):
    token: str = Field(..., min_length=1)
    title: Optional[str] = None
    body: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PushSendToTopicRequest(BaseSchema):
    topic: str = Field(..., min_length=1)
    title: Optional[str] = None
    body: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PushSendToUserRequest(BaseSchema):
    user_id: int = Field(..., gt=0)
    title: Optional[str] = None
    body: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
