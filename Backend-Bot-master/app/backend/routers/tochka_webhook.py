from fastapi import APIRouter, Request, Body
from app.services.webhook_dispatcher import webhook_dispatcher


tochka_webhook_router = APIRouter()

@tochka_webhook_router.post("/webhooks/tochka", status_code=200)
async def tochka_webhook(request: Request, webhook: str = Body(..., media_type="text/plain")):
    session = request.state.session
    await webhook_dispatcher.dispatch_webhook(session, webhook)
    return {"ok": True}

