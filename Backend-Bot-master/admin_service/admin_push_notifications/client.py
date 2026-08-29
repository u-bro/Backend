import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class PushAPIError(Exception):
    def __init__(self, message, *, code=None, history_id=None):
        super().__init__(message)
        self.code = code
        self.history_id = history_id


class PushAPITimeout(PushAPIError):
    pass


def send_push(payload):
    token = settings.PUSH_INTERNAL_TOKEN
    if not token:
        raise PushAPIError("PUSH_INTERNAL_TOKEN не настроен.")

    try:
        response = requests.post(
            f"{settings.PUSH_API_BASE_URL.rstrip('/')}/api/v1/internal/push/send",
            json=payload,
            headers={"X-Push-Internal-Token": token},
            timeout=settings.PUSH_API_TIMEOUT,
        )
    except requests.Timeout as exc:
        logger.warning("Push API request timed out")
        raise PushAPITimeout("Backend не ответил вовремя. Не повторяйте отправку: проверьте историю.") from exc
    except requests.RequestException as exc:
        logger.exception("Push API request failed")
        raise PushAPIError("Backend push-уведомлений недоступен.") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        if isinstance(detail, dict):
            code = detail.get("code")
            history_id = detail.get("history_id")
            message = (
                "Такое push-уведомление уже отправлялось в последние 5 минут."
                if code == "ADMIN_PUSH_DUPLICATE_RECENT"
                else detail.get("message") or code
            )
            raise PushAPIError(message, code=code, history_id=history_id)
        raise PushAPIError(detail or f"Backend push-уведомлений вернул HTTP {response.status_code}.")
    return response.json()
