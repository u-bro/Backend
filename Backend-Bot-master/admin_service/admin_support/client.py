import logging
import os

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class SupportAPIError(Exception):
    pass


def support_action(conversation_id, action, operator_name, payload=None):
    token = (os.getenv("SUPPORT_INTERNAL_TOKEN") or "").strip()
    if not token:
        raise SupportAPIError("SUPPORT_INTERNAL_TOKEN не настроен.")

    endpoint = f"/api/v1/internal/support/conversations/{conversation_id}/{action}"
    try:
        response = requests.post(
            f"{settings.SUPPORT_API_BASE_URL.rstrip('/')}{endpoint}",
            json=payload,
            headers={
                "X-Support-Internal-Token": token,
                "X-Support-Operator": operator_name[:150],
            },
            timeout=settings.SUPPORT_API_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Support API request failed")
        raise SupportAPIError("Backend поддержки недоступен.") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        raise SupportAPIError(detail or f"Backend поддержки вернул HTTP {response.status_code}.")
    return response.json()
