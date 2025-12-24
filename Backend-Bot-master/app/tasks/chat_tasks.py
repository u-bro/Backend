import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.tasks.celery_app import celery_app
from app.db import async_session_maker
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)


async def _save_message_async(payload: dict) -> Optional[dict]:
    async with async_session_maker() as session:
        try:
            # payload expected keys: ride_id, sender_id, text, receiver_id, message_type, attachments, idempotency_key
            ride_id = payload.get("ride_id")
            sender_id = payload.get("sender_id")
            receiver_id = payload.get("receiver_id")
            text = payload.get("text")
            message_type = payload.get("message_type", "text")
            attachments = payload.get("attachments")

            # Use chat_service to persist
            result = await chat_service.save_message(
                session=session,
                ride_id=ride_id,
                sender_id=sender_id,
                text=text,
                message_type=message_type,
                receiver_id=receiver_id,
                attachments=attachments,
                is_moderated=True,
                idempotency_key=payload.get("idempotency_key"),
            )

            return result.model_dump() if hasattr(result, 'model_dump') else None
        except Exception as e:
            logger.exception("Failed to save chat message in async task: %s", e)
            raise


@celery_app.task(bind=True, max_retries=5, default_retry_delay=10)
def save_chat_message(self, payload: dict) -> Optional[dict]:
    """Celery task to persist chat message using async DB session."""
    try:
        # Run async save in event loop
        result = asyncio.run(_save_message_async(payload))
        return result
    except Exception as exc:
        try:
            # exponential backoff handled by Celery retries
            raise self.retry(exc=exc, countdown=min(60, (self.request.retries + 1) * 5))
        except Exception:
            logger.exception("Final failure saving chat message: %s", exc)
            raise
