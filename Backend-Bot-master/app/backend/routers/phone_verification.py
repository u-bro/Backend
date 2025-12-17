from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse
from app.backend.routers.base import BaseRouter
from app.crud.phone_verification import phone_verification_crud
from app.schemas.phone_verification import PhoneVerificationSchema, PhoneVerificationCreate, PhoneVerificationUpdate, PhoneVerificationSchemaCreate, PhoneVerificationVerifyRequest
from app.backend.deps.get_current_user import get_current_user, get_current_user_id
from app.backend.deps import require_role_unverified
from app.config import TELEGRAM_OTP_BASE_URL, TELEGRAM_OTP_TOKEN
from app.logger import logger
from app.models import User
import aiohttp, secrets
from datetime import datetime

class PhoneVerificationRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(phone_verification_crud, "/phone-verifications")

    def setup_routes(self) -> None:
        self.router.add_api_route(self.prefix, self.get_paginated, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.get_by_id, methods=["GET"], status_code=200)
        self.router.add_api_route(self.prefix, self.create_item, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.update_item, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.delete_item, methods=["DELETE"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/send", self.send_telegram_otp, methods=["POST"], status_code=200, dependencies=[Depends(require_role_unverified(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/verify", self.verify_telegram_otp, methods=["POST"], status_code=200, dependencies=[Depends(require_role_unverified(["user", "driver", "admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[PhoneVerificationSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[PhoneVerificationSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> PhoneVerificationSchema:
        return await super().get_by_id(request, item_id)

    async def create_item(self, request: Request, body: PhoneVerificationCreate) -> PhoneVerificationSchema:
        try:
            return await self.model_crud.create(request.state.session, body)
        except IntegrityError as e:
            await request.state.session.rollback()
            return JSONResponse(
                status_code=422,
                content={"detail": f"Foreign key constraint violation: {str(e.orig)}"}
            )

    async def update_item(self, request: Request, item_id: int, body: PhoneVerificationUpdate) -> PhoneVerificationSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete_item(self, request: Request, item_id: int):
        item = await self.model_crud.delete(request.state.session, item_id)
        if item is None:
            return JSONResponse(status_code=404, content={"detail": "Item not found"})
        return item

    async def send_telegram_otp(
        self,
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> PhoneVerificationSchema:
        user_id = current_user.id
        phone_number = getattr(current_user, "phone", None)
        if not phone_number:
            return JSONResponse(status_code=400, content={"detail": "User phone is not set"})

        url = f"{TELEGRAM_OTP_BASE_URL}sendVerificationMessage"
        headers = {
            'Authorization': f'Bearer {TELEGRAM_OTP_TOKEN}',
            'Content-Type': 'application/json'
        }
        code = self.generate_otp()
        ttl = 120
        json_body = {
            'phone_number': phone_number,
            'code': code,
            'ttl': ttl,
        }
        logger.info(json_body)

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, json=json_body) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        if not response_json.get('ok'):
                            error_message = response_json.get('error', 'Unknown error')
                            logger.error(f"Telegram OTP Error: {error_message}")
                            return JSONResponse(status_code=400, content={"detail": error_message})
                        
                        updated_at_timestamp = response_json.get('result', {}).get('delivery_status', {}).get('updated_at', 0)
                        expires_at_timestamp = updated_at_timestamp + ttl
                        expires_at = datetime.utcfromtimestamp(expires_at_timestamp)
                        
                        create_obj = PhoneVerificationSchemaCreate(
                            user_id=user_id,
                            phone=phone_number,
                            code=code,
                            expires_at=expires_at
                        )
                        return await super().create(request, create_obj)
                    else:
                        logger.error(f"Failed to send OTP: HTTP {response.status}")
                        return JSONResponse(status_code=400, content={"detail": f"Failed to send OTP: HTTP {response.status}"})
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    async def verify_telegram_otp(self, request: Request, verify_obj: PhoneVerificationVerifyRequest, user_id: int = Depends(get_current_user_id)) -> JSONResponse:
        item = await self.model_crud.get_by_user_id(request.state.session, user_id)
        if item is None:
            return JSONResponse(status_code=404, content={"detail": "No phone verification record found"})
        
        if verify_obj.code == item.code:
            updated_item = await self.model_crud.update_status_by_user_id(request.state.session, user_id, "confirmed")
            if updated_item:
                return JSONResponse(status_code=200, content={"detail": "Code verified and status updated"})
            else:
                return JSONResponse(status_code=500, content={"detail": "Failed to update verification status"})
        
        return JSONResponse(status_code=401, content={"detail": "Code incorrect"})

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

phone_verification_router = PhoneVerificationRouter().router
