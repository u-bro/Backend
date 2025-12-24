from app.crud.base import CrudBase
from app.models.phone_verification import PhoneVerification
from app.schemas.phone_verification import PhoneVerificationSchema
from app.models.phone_verification import PhoneVerification
from app.schemas import PhoneVerificationSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, desc
from app.schemas.phone_verification import PhoneVerificationVerifyRequest
from datetime import datetime, timedelta
from app.config import OTP_CONFIRMED_EXPIRATION_HOURS, JWT_EXPIRATION_HOURS
from .auth import auth_crud
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

    async def verify_by_user_id(self, session: AsyncSession, verify_obj: PhoneVerificationVerifyRequest) -> str | None:
        item = await self.get_by_phone(session, verify_obj.phone)

        if item.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=400, detail='Code expired')

        if item is None or verify_obj.code != item.code or item.status == 'confirmed':
            raise HTTPException(status_code=400, detail='Code is not correct')

        stmt = (
            update(self.model)
            .where(self.model.id == item.id)
            .values(status="confirmed", expires_at=item.expires_at + timedelta(hours=OTP_CONFIRMED_EXPIRATION_HOURS))
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        self.schema.model_validate(result)

        return auth_crud.create_access_token(item.user_id, timedelta(hours=JWT_EXPIRATION_HOURS))


phone_verification_crud = PhoneVerificationCrud()
