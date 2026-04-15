from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.logger import logger
from app.crud import commission_payment_crud, ride_crud, in_app_notification_crud, driver_profile_crud
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.ride import RideschemaUpdateAfterCommission
from .websocket_manager import manager_driver_feed
from app.crud.driver_location_sender import driver_location_sender
from .tbank_acquiring import amount_to_minor_units, tbank_acquiring_client


SUCCESS_PAYMENT_STATUSES = {"CONFIRMED"}
FAILED_PAYMENT_STATUSES = {"AUTH_FAIL", "REJECTED", "DEADLINE_EXPIRED", "CANCELED", "CANCELLED"}


class WebhookDispatcher:
    async def dispatch_webhook(self, session: AsyncSession, payload: dict, *, verify_token: bool = True):
        if verify_token and not tbank_acquiring_client.verify_notification_token(payload):
            raise HTTPException(status_code=403, detail="Forbidden")
        await self._process_payment_update(session, payload)

    async def _process_payment_update(
        self,
        session: AsyncSession,
        payload: dict,
        *,
        emit_success_side_effects: bool = True,
        emit_failure_notifications: bool = True,
    ):
        payment_id = payload.get("PaymentId") or payload.get("paymentId")
        status = payload.get("Status") or payload.get("status")
        if not payment_id:
            raise HTTPException(status_code=400, detail="PaymentId is required")

        commission_payment = await commission_payment_crud.get_by_payment_id(session, str(payment_id))
        if not commission_payment:
            logger.warning(f"Commission payment not found for payment_id: {payment_id}")
            raise HTTPException(status_code=404, detail="Commission payment not found")

        payload_amount = payload.get("Amount")
        if payload_amount is not None:
            expected_amount = amount_to_minor_units(commission_payment.amount)
            if int(payload_amount) != expected_amount:
                logger.error(
                    "T-Bank payment amount mismatch for payment_id=%s: expected=%s got=%s",
                    payment_id,
                    expected_amount,
                    payload_amount,
                )
                raise HTTPException(status_code=400, detail="Payment amount mismatch")

        update_fields = {
            "payment_id": str(payment_id),
            "updated_at": datetime.now(timezone.utc),
        }
        if status:
            update_fields["status"] = status
        if status in SUCCESS_PAYMENT_STATUSES and not commission_payment.paid_at:
            update_fields["paid_at"] = datetime.now(timezone.utc)

        updated = await commission_payment_crud.update(session, commission_payment.id, update_fields)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update commission payment")

        if status in SUCCESS_PAYMENT_STATUSES and not commission_payment.paid_at and emit_success_side_effects:
            await self._handle_success(session, commission_payment, updated)
        elif status in FAILED_PAYMENT_STATUSES and emit_failure_notifications:
            await self._handle_failure(session, commission_payment, updated)

    async def _handle_success(self, session: AsyncSession, commission_payment, updated) -> None:
        ride = await ride_crud.get_by_id(session, commission_payment.ride_id)
        if not ride:
            return

        updated_ride = await ride_crud.update(session, ride.id, RideschemaUpdateAfterCommission(), updated.user_id)
        await in_app_notification_crud.create(session, InAppNotificationCreate(
            user_id=commission_payment.user_id,
            type='ride_status_changed',
            title="Комиссия оплачена",
            message="Проверьте информацию о поездке",
            data=updated_ride.model_dump(mode='json'),
            dedup_key=None,
        ))
        await in_app_notification_crud.create(session, InAppNotificationCreate(
            user_id=commission_payment.user_id,
            type='commission_payment',
            title='Комиссия оплачена',
            message='Ваша комиссия за поездку оплачена',
            data=updated.model_dump(mode='json'),
            dedup_key=str(commission_payment.id),
        ))
        driver_profile = await driver_profile_crud.get_by_id(session, ride.driver_profile_id)
        driver_id = driver_profile.user_id if driver_profile else 0
        await manager_driver_feed.send_personal_message(driver_id, {"type": "ride_commission_paid", "message": "Клиент оплатил комиссию за поездку", "data": updated_ride.model_dump(mode="json")})
        await driver_location_sender.start_task(updated_ride.client_id, updated_ride.driver_profile_id)

    async def _handle_failure(self, session: AsyncSession, commission_payment, updated) -> None:
        logger.warning("T-Bank acquiring payment failed: payment_id=%s status=%s", updated.payment_id, updated.status)
        await in_app_notification_crud.create(session, InAppNotificationCreate(
            user_id=commission_payment.user_id,
            type='commission_payment',
            title='Комиссия не оплачена',
            message=f'Ваша комиссия за поездку не оплачена. Текущий статус платежа: {updated.status}',
            data=updated.model_dump(mode='json'),
            dedup_key=f"failed_{commission_payment.id}_{updated.status}",
        ))


webhook_dispatcher = WebhookDispatcher()
