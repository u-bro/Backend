import asyncio
from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.commission_payment import CommissionPayment
from app.schemas.commission_payment import CommissionPaymentSchema
from app.schemas.ride import RideSchemaUpdateByClient
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from app.config import COMMISSION_PAY_SECONDS_LIMIT
from .ride import ride_crud
from app.services import manager_driver_feed
from app.services.chat_service import chat_service
from app.services.fcm_service import fcm_service
from .driver_tracker import driver_tracker
from app.db import async_session_maker
from .driver_profile import driver_profile_crud
from .in_app_notification import in_app_notification_crud


class CommissionPaymentCrud(CrudBase[CommissionPayment, CommissionPaymentSchema]):
    def __init__(self) -> None:
        super().__init__(CommissionPayment, CommissionPaymentSchema)

    async def get_by_operation_id(self, session: AsyncSession, operation_id: str) -> CommissionPaymentSchema | None:
        result = await session.execute(select(self.model).where(self.model.tochka_operation_id == operation_id))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def get_by_operation_id_sandbox(self, session: AsyncSession, operation_id: str) -> list[CommissionPaymentSchema]:
        result = await session.execute(select(self.model).where(and_(self.model.tochka_operation_id == operation_id, self.model.status == 'CREATED')))
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

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

    async def update_by_operation_id(self, session: AsyncSession, operation_id: str, fields: dict) -> CommissionPaymentSchema | None:
        existing = await self.get_by_operation_id(session, operation_id)
        if not existing:
            return None

        if not fields:
            return existing

        return await self.update(session, existing.id, fields)

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

    async def cancel_commission_payment_if_timeout(self, ride_id: int, user_id: int) -> None:
        await asyncio.sleep(COMMISSION_PAY_SECONDS_LIMIT)
        async with async_session_maker() as session:
            payment = await self.get_by_ride_and_user(session, ride_id, user_id)
            if not payment or payment.status != 'APPROVED':
                updated_ride = await ride_crud.update(session, ride_id, RideSchemaUpdateByClient(status='canceled'), user_id)
                driver_profile = await driver_profile_crud.get_by_id(session, updated_ride.driver_profile_id)
                await chat_service.save_message_and_send_to_ride(session=session, ride_id=ride_id, text="Клиент не оплатил комиссию вовремя", message_type="system")
                await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "ride_canceled", "message": "Клиент не оплатил комиссию вовремя"})
                await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=user_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена из-за истечения срока оплаты комиссии", data=updated_ride, dedup_key=f"{updated_ride.id}_canceled"))
                await fcm_service.send_to_user(session, user_id, PushNotificationData(title='Поездка отменена', body='Поездка отменена из-за истечения срока оплаты комиссии'))
                await driver_tracker.release_ride(session, updated_ride.driver_profile_id)
            await session.commit()

commission_payment_crud = CommissionPaymentCrud()
