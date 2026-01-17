from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CrudBase
from app.models.commission_payment import CommissionPayment
from app.schemas.commission_payment import CommissionPaymentSchema


class CommissionPaymentCrud(CrudBase[CommissionPayment, CommissionPaymentSchema]):
    def __init__(self) -> None:
        super().__init__(CommissionPayment, CommissionPaymentSchema)

    async def get_by_operation_id(self, session: AsyncSession, operation_id: str) -> CommissionPaymentSchema | None:
        result = await session.execute(select(self.model).where(self.model.tochka_operation_id == operation_id))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def get_by_ride_and_user(self, session: AsyncSession, ride_id: int, user_id: int, *, is_refund: bool = False) -> CommissionPaymentSchema | None:
        result = await session.execute(
            select(self.model).where(
                self.model.ride_id == ride_id,
                self.model.user_id == user_id,
                self.model.is_refund == is_refund,
            )
        )
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def update(self, session: AsyncSession, id: int, fields: dict) -> CommissionPaymentSchema | None:
        if not fields:
            return await self.get_by_id(session, id)

        stmt = update(self.model).where(self.model.id == id).values(fields).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def create(self, session: AsyncSession, fields: dict) -> CommissionPaymentSchema:
        stmt = insert(self.model).values(fields).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result)


commission_payment_crud = CommissionPaymentCrud()
