from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx

from app.config import MAX_API_BASE_URL, MAX_BOT_TOKEN, MAX_BOT_USERNAME, MAX_SUPPORT_LINK_TEMPLATE, MAX_WEBHOOK_SECRET
from app.logger import logger


class MaxNotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True)
class MaxIncomingEvent:
    chat_id: int
    user_id: int | None
    external_message_id: str | None
    text: str | None
    update_type: str


class MaxBotService:
    """MAX integration boundary. MAX's transport and event contract stay outside the domain layer."""

    def __init__(self, sender: Callable[[int, str], Awaitable[None]] | None = None):
        self._sender = sender

    def build_support_link(self, user_id: int | None = None) -> str:
        template = MAX_SUPPORT_LINK_TEMPLATE or ("https://max.ru/{username}" if MAX_BOT_USERNAME else None)
        if not template:
            raise MaxNotConfiguredError("MAX_BOT_USERNAME is not configured")
        values = {"user_id": user_id or "", "username": MAX_BOT_USERNAME or ""}
        try:
            return template.format(**values)
        except (KeyError, ValueError):
            raise MaxNotConfiguredError("MAX_SUPPORT_LINK_TEMPLATE must use only {user_id} and {username}")

    def verify_webhook_secret(self, supplied_secret: str | None) -> bool:
        return not MAX_WEBHOOK_SECRET or supplied_secret == MAX_WEBHOOK_SECRET

    def parse_incoming_event(self, payload: dict[str, Any]) -> MaxIncomingEvent | None:
        """Parse the official MAX Update shape without leaking it into the domain."""
        update_type = payload.get("update_type")
        if update_type not in ("message_created", "bot_started"):
            return None
        if update_type == "bot_started":
            user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
            return self._make_event(
                chat_id=payload.get("chat_id"),
                user_id=user.get("user_id"),
                external_message_id=None,
                text=None,
                update_type=update_type,
            )

        message = payload.get("message")
        if not isinstance(message, dict):
            return None
        sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}
        recipient = message.get("recipient") if isinstance(message.get("recipient"), dict) else {}
        body = message.get("body") if isinstance(message.get("body"), dict) else {}
        text = body.get("text")
        if not isinstance(text, str) or not text.strip():
            return None
        return self._make_event(
            chat_id=recipient.get("chat_id"),
            user_id=sender.get("user_id"),
            external_message_id=body.get("mid") or message.get("id"),
            text=text.strip(),
            update_type=update_type,
        )

    @staticmethod
    def _make_event(
        *,
        chat_id: Any,
        user_id: Any,
        external_message_id: Any,
        text: str | None,
        update_type: str,
    ) -> MaxIncomingEvent | None:
        if chat_id is None:
            return None
        try:
            return MaxIncomingEvent(
                chat_id=int(chat_id),
                user_id=int(user_id) if user_id is not None else None,
                external_message_id=str(external_message_id) if external_message_id is not None else None,
                text=text,
                update_type=update_type,
            )
        except (TypeError, ValueError):
            return None

    async def send_message(self, chat_id: int, text: str) -> None:
        if self._sender:
            await self._sender(chat_id, text)
            return
        if not MAX_API_BASE_URL or not MAX_BOT_TOKEN:
            raise MaxNotConfiguredError("MAX message sending is not configured")
        url = f"{MAX_API_BASE_URL.rstrip('/')}/messages"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    url,
                    params={"chat_id": chat_id},
                    headers={
                        "Authorization": MAX_BOT_TOKEN,
                        "Content-Type": "application/json",
                    },
                    json={"text": text},
                )
        except httpx.HTTPError as exc:
            logger.error("[MAX] send failed: network error (%s)", type(exc).__name__)
            raise RuntimeError("MAX message delivery failed") from exc

        if not response.is_success:
            logger.error("[MAX] send failed: HTTP %s", response.status_code)
            raise RuntimeError(f"MAX message delivery failed with HTTP {response.status_code}")


max_bot_service = MaxBotService()
