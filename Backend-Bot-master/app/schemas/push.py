from typing import Any, Dict, Optional
from pydantic import Field
from .base import BaseSchema


class PushNotificationData(BaseSchema):
    title: Optional[str] = None
    body: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PushSendToTokenRequest(PushNotificationData):
    token: str = Field(..., min_length=1)


class PushSendToTopicRequest(PushNotificationData):
    topic: str = Field(..., min_length=1)


class PushSendToUserRequest(PushNotificationData):
    user_id: int = Field(..., gt=0)
