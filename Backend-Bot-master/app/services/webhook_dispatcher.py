import jwt, json
from jwt import exceptions, PyJWK
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.logger import logger
from app.config import TOCHKA_WEBHOOK_OPEN_KEY, TOCHKA_USE_SANDBOX
from app.crud import commission_payment_crud, ride_crud, in_app_notification_crud, driver_profile_crud
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.ride import RideschemaUpdateAfterCommission
from .websocket_manager import manager_driver_feed


class WebhookDispatcher:

    def __init__(self, key_json: str):
        key = json.loads(key_json)
        self.jwk_key = PyJWK(key)
        self._dispatcher = {
            'acquiringInternetPayment': self._dispatch_acquiring_internet_payment
        }
    
    def decode_webhook(self, payload: str):
        try:
            print(payload)
            webhook_jwt = jwt.decode(payload, self.jwk_key.key, algorithms=["RS256"])
        except exceptions.DecodeError:
            raise HTTPException(status_code=403, detail="Forbidden")
        except Exception as e:
            logger.error(f"Error decoding Tochka webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

        return webhook_jwt

    async def dispatch_webhook(self, session: AsyncSession, payload: str):
        webhook = self.decode_webhook(payload)
        webhook_type = webhook.get('webhookType')
        if webhook_type in self._dispatcher:
            await self._dispatcher[webhook_type](session, webhook)

    async def _dispatch_acquiring_internet_payment(self, session: AsyncSession, webhook: dict):
        status = webhook.get('status')
        operationId = webhook.get('operationId')
        if TOCHKA_USE_SANDBOX:
            commission_payments = await commission_payment_crud.get_by_operation_id_sandbox(session, operationId)
            commission_payment = commission_payments[0] if len(commission_payments) else None
        else:
            commission_payment = await commission_payment_crud.get_by_operation_id(session, operationId)
        if not commission_payment:
            logger.warning(f"Commission payment not found for operationId: {operationId}")
            raise HTTPException(status_code=404, detail="Commission payment not found")

        updated = await commission_payment_crud.update(session, commission_payment.id, {'status': status})
        if status == 'APPROVED':
            await in_app_notification_crud.create(session, InAppNotificationCreate(
                    user_id=commission_payment.user_id,
                    type='commission_payment',
                    title='Commission payment approved',
                    message='Your commission payment has been approved',
                    data=updated.model_dump(mode='json'),
                    dedup_key=str(commission_payment.id)
                ))
            ride = await ride_crud.get_by_id(session, commission_payment.ride_id)
            if ride:
                updated_ride = await ride_crud.update(session, ride.id, RideschemaUpdateAfterCommission(), updated.user_id)
                await in_app_notification_crud.create(session, InAppNotificationCreate(
                    user_id=commission_payment.user_id,
                    type='ride_status_changed',
                    title=f"Ride status is changed from \"{ride.status}\" to \"{updated_ride.status}\"",
                    message="Check ride info, client",
                    data=updated_ride.model_dump(mode='json'),
                    dedup_key=None
                ))
                driver_profile = await driver_profile_crud.get_by_id(session, ride.driver_profile_id)
                driver_id = driver_profile.user_id if driver_profile else 0
                await manager_driver_feed.send_personal_message(driver_id, {"type": "ride_commission_paid", "message": "Client has paid the commission for ride", "data": updated_ride.model_dump(mode="json")})
        else:
            logger.warning(f"Acquiring internet payment failed: {webhook}")
            await in_app_notification_crud.create(session, InAppNotificationCreate(
                    user_id=commission_payment.user_id,
                    type='commission_payment',
                    title='Commission payment failed',
                    message=f'Your commission payment has been failed. Current payment status: {status}',
                    data=updated.model_dump(mode='json'),
                    dedup_key=None
                ))
            raise HTTPException(status_code=400, detail="Payment failed")

webhook_dispatcher = WebhookDispatcher(TOCHKA_WEBHOOK_OPEN_KEY)
