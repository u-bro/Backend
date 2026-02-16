from fastapi import Request, Depends
from app.crud.phone_verification import phone_verification_crud
from app.crud.auth import CrudAuth, auth_crud
from app.crud.refresh_token import refresh_token_crud
from app.schemas import AuthSchemaLogin, PhoneVerificationSchema, TokenResponse, RefreshTokenVerifyRequest, TokenResponseRegister
from app.schemas.phone_verification import PhoneVerificationSchemaCreate, PhoneVerificationVerifyRequest
from app.backend.routers.base import BaseRouter
from app.models import User
from app.backend.deps import get_current_user_id
from app.config import OTP_TTL
import secrets
from datetime import datetime, timedelta, timezone

class AuthRouter(BaseRouter):
    def __init__(self, model_crud: CrudAuth, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/send", self.login_or_register, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/verify", self.verify_otp, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/refresh", self.refresh, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/logout", self.logout, methods=["POST"], status_code=200, dependencies=[Depends(get_current_user_id)])

    async def login_or_register(self, request: Request, login_obj: AuthSchemaLogin) -> PhoneVerificationSchema:
        user, is_registred = await self.model_crud.login_or_register(request.state.session, login_obj.phone)
        return await self.send_otp(request, user, is_registred)

    async def send_otp(self, request: Request, user: User, is_registred: bool) -> PhoneVerificationSchema:
        code = self.generate_otp()
        ttl = OTP_TTL
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        create_obj = PhoneVerificationSchemaCreate(
            user_id=user.id,
            phone=user.phone,
            code=code,
            expires_at=expires_at,
            is_registred=is_registred
        )
        return await phone_verification_crud.create(request.state.session, create_obj)

    async def verify_otp(self, request: Request, verify_obj: PhoneVerificationVerifyRequest) -> TokenResponseRegister:
        return await phone_verification_crud.verify_by_user_id(request.state.session, verify_obj)

    async def refresh(self, request: Request, refresh_obj: RefreshTokenVerifyRequest) -> TokenResponse:
        return await self.model_crud.refresh(request.state.session, refresh_obj)

    async def logout(self, request: Request, refresh_obj: RefreshTokenVerifyRequest) -> dict:
        await refresh_token_crud.revoke(request.state.session, refresh_obj.refresh_token)
        return {"ok": True}

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

auth_router = AuthRouter(auth_crud, "/auth").router
