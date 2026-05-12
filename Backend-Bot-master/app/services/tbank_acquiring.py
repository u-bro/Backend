import hashlib, hmac
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from app.config import COMMISSION_PAY_SECONDS_LIMIT
from typing import Any, Mapping
import aiohttp
from app.config import (
    TBANK_BASE_URL,
    TBANK_SANDBOX_URL,
    TBANK_TERMINAL_KEY,
    TBANK_TERMINAL_PASSWORD,
    TBANK_USE_SANDBOX,
)


def _stringify_tbank_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def make_tbank_token(payload: Mapping[str, Any], password: str) -> str:
    token_parts: dict[str, str] = {}
    for key, value in payload.items():
        if key == "Token" or value is None or isinstance(value, (dict, list, tuple, set)):
            continue
        token_parts[str(key)] = _stringify_tbank_value(value)

    token_parts["Password"] = password
    raw = "".join(token_parts[key] for key in sorted(token_parts))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_tbank_notification_token(payload: Mapping[str, Any], password: str) -> bool:
    token = payload.get("Token")
    if not token:
        return False
    expected_token = make_tbank_token(payload, password)
    return hmac.compare_digest(str(token), expected_token)


def amount_to_minor_units(amount: float | Decimal | int | str) -> int:
    normalized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int((normalized * 100).to_integral_value(rounding=ROUND_HALF_UP))


class TBankAPIError(RuntimeError):
    def __init__(self, status: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class TBankAcquiringClient:
    def __init__(self) -> None:
        self._timeout = aiohttp.ClientTimeout(total=30)

    def _base_url(self) -> str:
        url = TBANK_SANDBOX_URL if TBANK_USE_SANDBOX else TBANK_BASE_URL
        return url if url.endswith("/") else (url + "/")

    @property
    def terminal_key(self) -> str:
        if not TBANK_TERMINAL_KEY:
            raise TBankAPIError(500, "Missing TBANK_TERMINAL_KEY")
        return TBANK_TERMINAL_KEY

    @property
    def terminal_password(self) -> str:
        if not TBANK_TERMINAL_PASSWORD:
            raise TBankAPIError(500, "Missing TBANK_TERMINAL_PASSWORD")
        return TBANK_TERMINAL_PASSWORD

    def make_token(self, payload: Mapping[str, Any]) -> str:
        return make_tbank_token(payload, self.terminal_password)

    def verify_notification_token(self, payload: Mapping[str, Any]) -> bool:
        return verify_tbank_notification_token(payload, self.terminal_password)

    async def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = dict(payload)
        body["Token"] = self.make_token(body)
        url = self._base_url() + path.lstrip("/")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                try:
                    response_payload = await resp.json(content_type=None)
                except Exception:
                    response_payload = {"raw": await resp.text()}

        if resp.status >= 400:
            raise TBankAPIError(resp.status, f"T-Bank API error {resp.status}", response_payload)

        if response_payload.get("Success") is False:
            message = response_payload.get("Details") or response_payload.get("Message") or response_payload.get("ErrorCode") or "T-Bank API request failed"
            raise TBankAPIError(resp.status, str(message), response_payload)

        return response_payload

    async def init_payment(
        self,
        *,
        amount: float | Decimal,
        order_id: str,
        description: str,
        success_url: str | None = None,
        fail_url: str | None = None,
        notification_url: str | None = None,
        receipt_data: dict[str, Any] | None = None,
        time_difference_seconds: int = 0,
    ) -> dict[str, Any]:
        if time_difference_seconds >= COMMISSION_PAY_SECONDS_LIMIT:
            raise TBankAPIError(400, "Слишком поздно для оплаты комиссии", {})

        payload: dict[str, Any] = {
            "TerminalKey": self.terminal_key,
            "Amount": amount_to_minor_units(amount),
            "OrderId": order_id,
            "Description": description[:140],
            "PayType": "O",
            "DATA": {
                "OperationInitiatorType": "0",
            },
            **({"Receipt": receipt_data} if receipt_data else {}),
            "RedirectDueDate": (datetime.now(timezone.utc) + timedelta(seconds=COMMISSION_PAY_SECONDS_LIMIT-time_difference_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if success_url:
            payload["SuccessURL"] = success_url
        if fail_url:
            payload["FailURL"] = fail_url
        if notification_url:
            payload["NotificationURL"] = notification_url

        return await self._request("/Init", payload)

    async def get_payment_state(self, payment_id: str) -> dict[str, Any]:
        payload = {
            "TerminalKey": self.terminal_key,
            "PaymentId": str(payment_id),
        }
        return await self._request("/GetState", payload)

    async def send_closing_receipt(self, payment_id: str, receipt_data: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "TerminalKey": self.terminal_key,
            "PaymentId": str(payment_id),
            "Receipt": receipt_data,
        }
        return await self._request("/SendClosingReceipt", payload)

tbank_acquiring_client = TBankAcquiringClient()
