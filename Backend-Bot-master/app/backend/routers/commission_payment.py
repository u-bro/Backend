from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from app.backend.deps import require_role, require_owner
from app.config import TOCHKA_ACQUIRING_FAIL_REDIRECT_URL, TOCHKA_ACQUIRING_REDIRECT_URL
from app.crud import ride_crud, commission_crud, commission_payment_crud
from app.schemas.commission_payment import CommissionPaymentCreateRequest, CommissionPaymentSchema
from app.services.tochka_acquiring import TochkaAPIError, tochka_acquiring_client
from app.models import Ride


commission_payment_router = APIRouter()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        v = value
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _to_float(v: float | Decimal | None) -> float:
    if v is None:
        return 0.0
    return float(v)


@commission_payment_router.post(
    "/commissions/{id}/payment-link",
    status_code=201,
    response_model=CommissionPaymentSchema,
    dependencies=[Depends(require_owner(Ride, "client_id"))],
)
async def create_commission_payment_link(request: Request, id: int, body: CommissionPaymentCreateRequest, user=Depends(require_role(["user", "driver", "admin"]))) -> CommissionPaymentSchema:
    session = request.state.session

    ride = await ride_crud.get_by_id(session, id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    existing = await commission_payment_crud.get_by_ride_and_user(session, id, user.id, is_refund=False)
    if existing and existing.payment_link:
        return existing

    # Base amount for commission calculation
    base_fare = getattr(ride, "actual_fare", None) or getattr(ride, "expected_fare", None)
    if base_fare is None:
        raise HTTPException(status_code=400, detail="Ride fare is not available")

    commission = await commission_crud.get_by_id(session, int(getattr(ride, "commission_id", 0) or 0))
    if not commission:
        raise HTTPException(status_code=400, detail="Ride commission is not configured")

    percentage = _to_float(getattr(commission, "percentage", 0))
    fixed_amount = _to_float(getattr(commission, "fixed_amount", 0))
    amount = _to_float(base_fare) * (percentage / 100.0) + fixed_amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Commission amount must be positive")

    purpose = f"Commission for ride #{id}"

    redirect_url = body.redirect_url or TOCHKA_ACQUIRING_REDIRECT_URL
    fail_redirect_url = body.fail_redirect_url or TOCHKA_ACQUIRING_FAIL_REDIRECT_URL

    raw_request = {
        "amount": float(amount),
        "purpose": purpose,
        "paymentMode": body.payment_mode,
        "redirectUrl": redirect_url,
        "failRedirectUrl": fail_redirect_url,
    }

    try:
        resp = await tochka_acquiring_client.create_payment_link(
            amount=float(amount),
            purpose=purpose,
            payment_mode=list(body.payment_mode),
            redirect_url=redirect_url,
            fail_redirect_url=fail_redirect_url,
        )
    except TochkaAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    data = (resp or {}).get("Data") or {}

    fields = {
        "ride_id": id,
        "user_id": user.id,
        "amount": amount,
        "currency": "RUB",
        "status": data.get("status") or "CREATED",
        "tochka_operation_id": data.get("operationId"),
        "payment_link": data.get("paymentLink"),
        "purpose": data.get("purpose") or purpose,
        "payment_mode": data.get("paymentMode") or list(body.payment_mode),
        "raw_request": raw_request,
        "raw_response": resp,
        "updated_at": datetime.now(timezone.utc),
    }

    if existing:
        updated = await commission_payment_crud.update_fields(session, existing.id, fields)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update commission payment")
        return updated

    created = await commission_payment_crud.create_row(session, {**fields, "created_at": datetime.now(timezone.utc)})
    return created


@commission_payment_router.get(
    "/commissions/payments/{payment_id}",
    status_code=200,
    response_model=CommissionPaymentSchema,
)
async def get_commission_payment(request: Request, payment_id: int, refresh: bool = False, user=Depends(require_role(["user", "admin"]))) -> CommissionPaymentSchema:
    session = request.state.session
    item = await commission_payment_crud.get_by_id(session, payment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Commission payment not found")

    if getattr(item, "user_id", None) != getattr(user, "id", None) and getattr(user, "role", None) and getattr(user.role, "code", None) != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    if not refresh or not item.tochka_operation_id:
        return item

    try:
        resp = await tochka_acquiring_client.get_payment_operation_info(item.tochka_operation_id)
    except TochkaAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    operations = (((resp or {}).get("Data") or {}).get("Operation")) or []
    op = operations[0] if operations else {}

    fields: dict = {
        "raw_response": resp,
        "updated_at": datetime.now(timezone.utc),
    }

    if isinstance(op, dict):
        if op.get("status"):
            fields["status"] = op.get("status")
        if op.get("paidAt"):
            parsed = _parse_dt(op.get("paidAt"))
            if parsed:
                fields["paid_at"] = parsed
        if op.get("paymentId"):
            fields["payment_id"] = op.get("paymentId")
        if op.get("transactionId"):
            fields["transaction_id"] = op.get("transactionId")

    updated = await commission_payment_crud.update_fields(session, item.id, fields)
    return updated or item
