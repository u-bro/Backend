import json
from urllib.parse import parse_qs
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from app.services.webhook_dispatcher import webhook_dispatcher

tbank_webhook_router = APIRouter()


async def _read_notification_payload(request: Request) -> dict:
    try:
        payload = await request.json()
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    try:
        form = await request.form()
        if form:
            return {key: value for key, value in form.items()}
    except Exception:
        pass

    raw_body = await request.body()
    if raw_body:
        try:
            payload = json.loads(raw_body)
            if isinstance(payload, dict):
                return payload
        except Exception:
            parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
            if parsed:
                return {key: values[-1] for key, values in parsed.items()}

    raise HTTPException(status_code=400, detail="Invalid webhook payload")


@tbank_webhook_router.post("/webhooks/tbank", status_code=200)
async def tbank_webhook(request: Request):
    session = request.state.session
    payload = await _read_notification_payload(request)
    await webhook_dispatcher.dispatch_webhook(session, payload)
    return PlainTextResponse("OK")
