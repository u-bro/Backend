from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema


class CommissionPaymentCreateRequest(BaseSchema):
    payment_mode: list[Literal["sbp", "card", "tinkoff", "dolyame"]] = Field(default_factory=lambda: ["card"])
    redirect_url: str | None = None
    fail_redirect_url: str | None = None


class CommissionPaymentSchema(BaseSchema):
    id: int
    ride_id: int
    user_id: int

    amount: float
    currency: str

    status: str

    tochka_operation_id: str | None = None
    payment_link: str | None = None

    purpose: str | None = None
    payment_mode: Any | None = None

    paid_at: datetime | None = None
    payment_id: str | None = None
    transaction_id: str | None = None

    is_refund: bool

    created_at: datetime | None = None
    updated_at: datetime | None = None


class CommissionPaymentWebhookIn(BaseSchema):
    payload: Any
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
