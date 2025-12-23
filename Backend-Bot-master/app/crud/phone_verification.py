from app.crud.base import CrudBase
from app.models.phone_verification import PhoneVerification
from app.schemas.phone_verification import PhoneVerificationSchema
from app.models.phone_verification import PhoneVerification
from app.schemas import PhoneVerificationSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, desc
from app.schemas.phone_verification import PhoneVerificationVerifyRequest
from datetime import datetime


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

    async def verify_by_user_id(self, session: AsyncSession, verify_obj: PhoneVerificationVerifyRequest, user_id: int) -> PhoneVerificationSchema | None:
        item = await self.get_by_user_id(session, user_id)
        if item is None or verify_obj.code != item.code:
            return 'Code is not correct'

        if item.expires_at <= datetime.utcnow():
            return 'Code expired'

        stmt = (
            update(self.model)
            .where(self.model.id == item.id)
            .values(status="confirmed")
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


phone_verification_crud = PhoneVerificationCrud()
