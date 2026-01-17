from datetime import datetime, timezone
from fastapi import APIRouter, Request
from app.crud.commission_payment import commission_payment_crud
from app.logger import logger


tochka_webhook_router = APIRouter()


def _find_first(d: object, keys: list[str]) -> object | None:
    if isinstance(d, dict):
        for k in keys:
            if k in d:
                return d[k]
        for v in d.values():
            found = _find_first(v, keys)
            if found is not None:
                return found
    elif isinstance(d, list):
        for item in d:
            found = _find_first(item, keys)
            if found is not None:
                return found
    return None


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        v = value
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)
    except Exception:
        return None


@tochka_webhook_router.post("/webhooks/tochka", status_code=200)
async def tochka_webhook(request: Request, payload: dict):
    session = request.state.session

    operation_id = _find_first(payload, ["operationId", "operation_id"])
    status = _find_first(payload, ["status"])
    paid_at = _find_first(payload, ["paidAt", "paid_at"])

    if not operation_id:
        logger.warning(f"Tochka webhook received without operationId: {payload}")
        return {"ok": True}

    existing = await commission_payment_crud.get_by_operation_id(session, str(operation_id))
    if not existing:
        logger.warning(f"Tochka webhook operationId not found in DB: {operation_id}")
        return {"ok": True}

    fields: dict = {"raw_response": payload, "updated_at": datetime.now(timezone.utc)}
    if status is not None:
        fields["status"] = str(status)
    if paid_at is not None:
        parsed = _parse_dt(paid_at)
        if parsed is not None:
            fields["paid_at"] = parsed

    await commission_payment_crud.update(session, existing.id, fields)
    return {"ok": True}
