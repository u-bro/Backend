import asyncio
import time
from typing import Any

import aiohttp

from app.config import (
    TOCHKA_BASE_URL,
    TOCHKA_SANDBOX_URL,
    TOCHKA_USE_SANDBOX,
    TOCHKA_OAUTH_TOKEN_URL,
    TOCHKA_OAUTH_CLIENT_ID,
    TOCHKA_OAUTH_CLIENT_SECRET,
    TOCHKA_OAUTH_SCOPE,
    TOCHKA_ACQUIRING_CUSTOMER_CODE,
    TOCHKA_ACQUIRING_MERCHANT_ID,
)


class TochkaAuthError(RuntimeError):
    pass


class TochkaAPIError(RuntimeError):
    def __init__(self, status: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class TochkaAcquiringClient:
    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    def _base_url(self) -> str:
        url = TOCHKA_SANDBOX_URL if TOCHKA_USE_SANDBOX else TOCHKA_BASE_URL
        return url if url.endswith("/") else (url + "/")

    async def _get_access_token(self) -> str:
        if TOCHKA_USE_SANDBOX:
            return "sandbox.jwt.token"

        if self._token and time.time() < (self._token_expires_at - 30):
            return self._token

        async with self._lock:
            if self._token and time.time() < (self._token_expires_at - 30):
                return self._token

            if not TOCHKA_OAUTH_CLIENT_ID or not TOCHKA_OAUTH_CLIENT_SECRET:
                raise TochkaAuthError("Missing TOCHKA_OAUTH_CLIENT_ID/TOCHKA_OAUTH_CLIENT_SECRET")

            data = {
                "grant_type": "client_credentials",
                "client_id": TOCHKA_OAUTH_CLIENT_ID,
                "client_secret": TOCHKA_OAUTH_CLIENT_SECRET,
                "scope": TOCHKA_OAUTH_SCOPE,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(TOCHKA_OAUTH_TOKEN_URL, data=data) as resp:
                    payload = await resp.json(content_type=None)
                    if resp.status != 200:
                        raise TochkaAuthError(f"Tochka token error HTTP {resp.status}: {payload}")

            token = payload.get("access_token")
            expires_in = payload.get("expires_in", 3600)
            if not token:
                raise TochkaAuthError(f"Tochka token response missing access_token: {payload}")

            self._token = token
            self._token_expires_at = time.time() + float(expires_in)
            return token

    async def _request(self, method: str, path: str, *, json_body: Any | None = None, params: dict | None = None) -> Any:
        token = await self._get_access_token()

        url = self._base_url() + path.lstrip("/")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_body, params=params, headers=headers) as resp:
                payload = await resp.json(content_type=None)
                print(json_body)
                print(payload)
                if resp.status >= 400:
                    raise TochkaAPIError(resp.status, f"Tochka API error {resp.status}", payload)
                return payload

    async def create_payment_link(self, *, amount: float, purpose: str, payment_mode: list[str], redirect_url: str | None = None, fail_redirect_url: str | None = None) -> dict:
        if not TOCHKA_ACQUIRING_CUSTOMER_CODE:
            raise TochkaAPIError(500, "Missing TOCHKA_ACQUIRING_CUSTOMER_CODE")

        data: dict[str, Any] = {
            "customerCode": TOCHKA_ACQUIRING_CUSTOMER_CODE,
            "amount": float(amount),
            "purpose": purpose,
            "paymentMode": payment_mode,
        }

        if TOCHKA_ACQUIRING_MERCHANT_ID:
            data["merchantId"] = TOCHKA_ACQUIRING_MERCHANT_ID

        if redirect_url:
            data["redirectUrl"] = redirect_url
        if fail_redirect_url:
            data["failRedirectUrl"] = fail_redirect_url

        return await self._request("POST", "/acquiring/v1.0/payments", json_body={"Data": data})

    async def get_payment_operation_info(self, operation_id: str) -> dict:
        return await self._request("GET", f"/acquiring/v1.0/payments/{operation_id}")


tochka_acquiring_client = TochkaAcquiringClient()
