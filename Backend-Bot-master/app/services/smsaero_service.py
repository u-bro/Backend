import aiohttp
from app.config import SMSAERO_EMAIL, SMSAERO_API_KEY
from fastapi import HTTPException
from typing import Any
from app.logger import logger

class SmsaeroService:
    def __init__(self):
        self.email = SMSAERO_EMAIL
        self.api_key = SMSAERO_API_KEY
        self.api_url = f"https://{self.email}:{self.api_key}@gate.smsaero.ru/v2/"
    
    async def send_sms(self, phone: str, sign: str, message: str) -> None:
        try:
            await self._request("POST", "/sms/send", params={
                "number": phone,
                "text": message,
                "sign": sign
            })
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
    
    async def _request(self, method: str, path: str, *, json_body: Any | None = None, params: dict | None = None) -> Any:
        url = self.api_url + path.lstrip("/")
        headers = {
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_body, params=params, headers=headers) as resp:
                payload = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise HTTPException(resp.status, f"Smsaero API error {resp.status}: {payload}")
                return payload

smsaero_service = SmsaeroService()