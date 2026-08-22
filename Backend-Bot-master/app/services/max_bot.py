from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.config import MAX_API_BASE_URL, MAX_BOT_TOKEN, MAX_SUPPORT_LINK_TEMPLATE, MAX_WEBHOOK_SECRET


class MaxNotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True)
class MaxIncomingEvent:
    chat_id: int
    user_id: int | None
    external_message_id: str | None
    text: str


class MaxBotService:
    """MAX integration boundary. MAX's transport and event contract stay outside the domain layer."""

    def __init__(self, sender: Callable[[int, str], Awaitable[None]] | None = None):
        self._sender = sender

    def build_support_link(self, user_id: int | None = None) -> str:
        if not MAX_SUPPORT_LINK_TEMPLATE:
            raise MaxNotConfiguredError("MAX_SUPPORT_LINK_TEMPLATE is not configured")
        values = {"user_id": user_id or "", "username": MAX_BOT_USERNAME or ""}
        try:
            return MAX_SUPPORT_LINK_TEMPLATE.format(**values)
        except (KeyError, ValueError):
            raise MaxNotConfiguredError("MAX_SUPPORT_LINK_TEMPLATE must use only {user_id} and {username}")

    def verify_webhook_secret(self, supplied_secret: str | None) -> bool:
        return not MAX_WEBHOOK_SECRET or supplied_secret == MAX_WEBHOOK_SECRET

    def parse_incoming_event(self, payload: dict[str, Any]) -> MaxIncomingEvent | None:
        """Parse only the small adapter shape; provider-specific mapping belongs here."""
        event_type = payload.get("event") or payload.get("type")
        if event_type not in (None, "message", "MESSAGE", "message_created"):
            return None
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        chat_id = payload.get("chat_id", message.get("chat_id"))
        user_id = payload.get("user_id", message.get("user_id"))
        message_id = payload.get("message_id", message.get("id"))
        text = payload.get("text", message.get("text"))
        if chat_id is None or not isinstance(text, str) or not text.strip():
            return None
        try:
            return MaxIncomingEvent(int(chat_id), int(user_id) if user_id is not None else None, str(message_id) if message_id is not None else None, text.strip())
        except (TypeError, ValueError):
            return None

    async def send_message(self, chat_id: int, text: str) -> None:
        if self._sender:
            await self._sender(chat_id, text)
            return
        if not MAX_API_BASE_URL or not MAX_BOT_TOKEN:
            raise MaxNotConfiguredError("MAX message sending is not configured")
        raise MaxNotConfiguredError("MAX API adapter is not implemented because the MAX API contract is unknown")


max_bot_service = MaxBotService()
