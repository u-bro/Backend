from app.crud.base import CrudBase
from app.models.phone_verification import PhoneVerification
from app.schemas.phone_verification import PhoneVerificationSchema
from app.models.phone_verification import PhoneVerification
from app.schemas import PhoneVerificationSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, desc
from app.logger import logger


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

    async def update_status_by_user_id(self, session: AsyncSession, user_id: int, status: str) -> PhoneVerificationSchema | None:
        try:
            stmt = (
                update(self.model)
                .where(self.model.user_id == user_id)
                .values(status=status)
                .returning(self.model)
            )
            result = await self.execute_get_one(session, stmt)
            return self.schema.model_validate(result) if result else None
        except Exception as e:
            logger.error(f"Error updating phone verification status: {e}")
            return None


phone_verification_crud = PhoneVerificationCrud()
