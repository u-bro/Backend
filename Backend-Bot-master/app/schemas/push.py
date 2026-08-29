from typing import Any, Dict, Literal, Optional
from pydantic import Field, model_validator
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


class AdminPushSendRequest(BaseSchema):
    audience: Literal["user", "all"]
    user_id: Optional[int] = Field(None, gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=2000)
    operator_id: int = Field(..., gt=0)
    operator_name: str = Field(..., min_length=1, max_length=150)

    @model_validator(mode="after")
    def validate_audience(self):
        if self.audience == "user" and self.user_id is None:
            raise ValueError("user_id is required for user audience")
        if self.audience == "all" and self.user_id is not None:
            raise ValueError("user_id must be empty for all audience")
        return self


class AdminPushSendResponse(BaseSchema):
    history_id: int
    status: Literal["sent", "partial", "failed", "unknown"]
    recipient_user_count: int
    attempted_token_count: int
    success_count: int
    failure_count: int
