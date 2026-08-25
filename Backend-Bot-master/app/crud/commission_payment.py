import asyncio
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.commission_payment import CommissionPayment
from app.schemas.commission_payment import CommissionPaymentSchema
from datetime import datetime, timezone
from app.schemas.ride_status_history import RideStatusHistoryCreate
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
from .ride_status_history import ride_status_history_crud
from app.services.after_commit import add_after_commit, commit_with_callbacks


class CommissionPaymentCrud(CrudBase[CommissionPayment, CommissionPaymentSchema]):
    def __init__(self) -> None:
        super().__init__(CommissionPayment, CommissionPaymentSchema)

    async def get_by_payment_id(self, session: AsyncSession, payment_id: str) -> CommissionPaymentSchema | None:
        result = await session.execute(select(self.model).where(self.model.payment_id == payment_id))
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

    async def cancel_commission_payment_if_timeout(self, ride_id: int, user_id: int) -> None:
        await asyncio.sleep(COMMISSION_PAY_SECONDS_LIMIT)
        async with async_session_maker() as session:
            payment = await self.get_by_ride_and_user(session, ride_id, user_id)
            if payment and (payment.status == 'CONFIRMED' or payment.status == 'AUTHORIZED'):
                return

            stmt = (
                update(ride_crud.model)
                .where(ride_crud.model.id == ride_id, ride_crud.model.status == "waiting_commission")
                .values(status="canceled", canceled_at=datetime.now(timezone.utc))
                .returning(ride_crud.model)
            )
            result = await ride_crud.execute_get_one(session, stmt)
            if not result:
                await commit_with_callbacks(session)
                return
            updated_ride = ride_crud.schema.model_validate(result)
            await ride_status_history_crud.create(
                session,
                RideStatusHistoryCreate(
                    ride_id=ride_id,
                    from_status="waiting_commission",
                    to_status="canceled",
                    changed_by=user_id,
                    created_at=datetime.now(timezone.utc),
                ),
            )
            driver_profile = await driver_profile_crud.get_by_id(session, updated_ride.driver_profile_id)
            await chat_service.save_message_and_send_to_ride(session=session, ride_id=ride_id, text="Клиент не оплатил комиссию вовремя", message_type="system")
            add_after_commit(session, lambda: manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "ride_canceled", "message": "Клиент не оплатил комиссию вовремя"}))
            await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=user_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена из-за истечения срока оплаты комиссии", data=updated_ride.model_dump(mode='json'), dedup_key=f"{updated_ride.id}_canceled"))
            add_after_commit(session, lambda: fcm_service.send_to_user(session, user_id, PushNotificationData(title='Поездка отменена', body='Поездка отменена из-за истечения срока оплаты комиссии')))
            await driver_tracker.release_ride(session, updated_ride.driver_profile_id)
            await commit_with_callbacks(session)

commission_payment_crud = CommissionPaymentCrud()
