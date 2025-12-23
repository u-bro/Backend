from typing import List
from fastapi import Request, Depends, HTTPException
from pydantic import TypeAdapter
from starlette.responses import JSONResponse
from app.backend.routers.base import BaseRouter
from app.crud.phone_verification import phone_verification_crud
from app.schemas.phone_verification import PhoneVerificationSchema, PhoneVerificationCreate, PhoneVerificationUpdate, PhoneVerificationSchemaCreate, PhoneVerificationVerifyRequest
from app.backend.deps.get_current_user import get_current_user, get_current_user_id
from app.backend.deps import require_role_unverified
from app.models import User
import secrets
from datetime import datetime, timedelta

class PhoneVerificationRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(phone_verification_crud, "/phone-verifications")

    def setup_routes(self) -> None:
        self.router.add_api_route(self.prefix, self.get_paginated, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.get_by_id, methods=["GET"], status_code=200)
        self.router.add_api_route(self.prefix, self.create_item, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.update, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{item_id}}", self.delete, methods=["DELETE"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/send", self.send_telegram_otp, methods=["POST"], status_code=200, dependencies=[Depends(require_role_unverified(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/verify", self.verify_telegram_otp, methods=["POST"], status_code=200, dependencies=[Depends(require_role_unverified(["user", "driver", "admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[PhoneVerificationSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[PhoneVerificationSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> PhoneVerificationSchema:
        return await super().get_by_id(request, item_id)

    async def create_item(self, request: Request, body: PhoneVerificationCreate) -> PhoneVerificationSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, item_id: int, body: PhoneVerificationUpdate) -> PhoneVerificationSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete(self, request: Request, item_id: int):
        return await self.model_crud.delete(request.state.session, item_id)

    async def send_telegram_otp(self, request: Request, current_user: User = Depends(get_current_user)) -> PhoneVerificationSchema:
        user_id = current_user.id
        phone_number = getattr(current_user, "phone", None)
        code = self.generate_otp()
        ttl = 120
        updated_at_timestamp = datetime.utcnow()
        expires_at = updated_at_timestamp + timedelta(seconds=ttl)
        create_obj = PhoneVerificationSchemaCreate(
            user_id=user_id,
            phone=phone_number,
            code=code,
            expires_at=expires_at
        )
        return await self.model_crud.create(request.state.session, create_obj)


    async def verify_telegram_otp(self, request: Request, verify_obj: PhoneVerificationVerifyRequest, user_id: int = Depends(get_current_user_id)) -> JSONResponse:
        return await self.model_crud.verify_by_user_id(request.state.session, verify_obj, user_id)

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

phone_verification_router = PhoneVerificationRouter().router
