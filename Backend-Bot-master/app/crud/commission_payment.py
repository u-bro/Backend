import asyncio
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.commission_payment import CommissionPayment
from app.schemas.commission_payment import CommissionPaymentSchema
from datetime import datetime, timezone
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
from app.services.after_commit import add_after_commit, commit_with_callbacks
from fastapi import HTTPException


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

            try:
                transition = await ride_crud.transition(
                    session,
                    ride_id,
                    "canceled",
                    {"waiting_commission"},
                    user_id,
                    values={
                        "canceled_at": datetime.now(timezone.utc),
                        "status_reason": "waiting_commission_timeout",
                    },
                )
            except HTTPException as exc:
                if exc.status_code != 409:
                    raise
                await commit_with_callbacks(session)
                return
            if not transition.changed:
                await commit_with_callbacks(session)
                return
            updated_ride = transition.ride
            driver_profile = await driver_profile_crud.get_by_id(session, updated_ride.driver_profile_id)
            await chat_service.save_message_and_send_to_ride(session=session, ride_id=ride_id, text="Клиент не оплатил комиссию вовремя", message_type="system")
            if driver_profile:
                payload = {"type": "ride_status_changed", "data": updated_ride.model_dump(mode="json"), "meta": {"previous_status": transition.previous_status, "actor": "system", "reason": "waiting_commission_timeout"}}
                add_after_commit(session, lambda driver_id=driver_profile.user_id, payload=payload: manager_driver_feed.send_personal_message(driver_id, payload))
            notification = await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=user_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена из-за истечения срока оплаты комиссии", data=updated_ride.model_dump(mode='json'), dedup_key=f"ride:{updated_ride.id}:canceled:commission_timeout"))
            if notification is not None:
                add_after_commit(session, lambda user_id=user_id: fcm_service.send_to_user_after_commit(user_id, PushNotificationData(title='Поездка отменена', body='Поездка отменена из-за истечения срока оплаты комиссии')))
            await driver_tracker.release_ride(session, updated_ride.driver_profile_id)
            await commit_with_callbacks(session)

commission_payment_crud = CommissionPaymentCrud()
