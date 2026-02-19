from app.crud.base import CrudBase
from app.models.phone_verification import PhoneVerification
from app.schemas.phone_verification import PhoneVerificationSchema, PhoneVerificationSchemaCreate
from app.schemas.auth import TokenResponseRegister
from app.schemas.refresh_token import RefreshTokenIn
from app.models.phone_verification import PhoneVerification
from app.schemas import PhoneVerificationSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, desc, insert
from app.schemas.phone_verification import PhoneVerificationVerifyRequest
from datetime import datetime, timedelta, timezone
from app.config import JWT_EXPIRATION_MINTUES, OTP_MAX_ATTEMPTS
from .auth import auth_crud
from .refresh_token import refresh_token_crud
from fastapi import HTTPException


class PhoneVerificationCrud(CrudBase[PhoneVerification, PhoneVerificationSchema]):
    def __init__(self) -> None:
        super().__init__(PhoneVerification, PhoneVerificationSchema)

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> PhoneVerificationSchema | None:
        result = await session.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .limit(1)
        )
        ver = result.scalar_one_or_none()
        return self.schema.model_validate(ver) if ver else None

    async def get_by_phone(self, session: AsyncSession, phone: str) -> PhoneVerificationSchema | None:
        result = await session.execute(
            select(self.model)
            .where(self.model.phone == phone)
            .order_by(desc(self.model.created_at))
            .limit(1)
        )
        ver = result.scalar_one_or_none()
        return self.schema.model_validate(ver) if ver else None

    async def verify_by_user_id(self, session: AsyncSession, verify_obj: PhoneVerificationVerifyRequest) -> TokenResponseRegister:
        item = await self.get_by_phone(session, verify_obj.phone)

        if item.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail='Code expired')

        if item is None or verify_obj.code != item.code or item.status == 'confirmed':
            raise HTTPException(status_code=400, detail='Code is not correct')

        stmt = (
            update(self.model)
            .where(self.model.id == item.id)
            .values(status="confirmed")
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        self.schema.model_validate(result)

        access_token = auth_crud.create_access_token(item.user_id, timedelta(minutes=JWT_EXPIRATION_MINTUES))
        refresh_token = await refresh_token_crud.create(session, RefreshTokenIn(user_id=item.user_id))
        return TokenResponseRegister(
            access_token=access_token,
            refresh_token=refresh_token.token,
            is_registred=item.is_registred
        )

    async def attempts_increment(self, session: AsyncSession, phone: str) -> PhoneVerificationSchema | None:
        existing = await self.get_by_phone(session, phone)
        if not existing:
            return None
        
        if existing.attempts > OTP_MAX_ATTEMPTS:
            raise HTTPException(status_code=400, detail='Too many attempts. Resend code')

        stmt = update(self.model).where(self.model.id == existing.id).values(attempts=self.model.attempts + 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def create(self, session: AsyncSession, create_obj: PhoneVerificationSchemaCreate) -> PhoneVerificationSchema | None:
        item = await self.get_by_phone(session, create_obj.phone)
        if item and item.next_sending_at and item.next_sending_at > datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail='Too many code sendings')

        stmt = insert(self.model).values(create_obj.model_dump()).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

phone_verification_crud = PhoneVerificationCrud()
