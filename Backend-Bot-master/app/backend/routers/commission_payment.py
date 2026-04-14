import asyncio
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from app.backend.deps import require_role, require_owner
from app.config import TBANK_PAYMENT_FAIL_REDIRECT_URL, TBANK_PAYMENT_NOTIFICATION_URL, TBANK_PAYMENT_REDIRECT_URL, TBANK_USE_SANDBOX
from app.crud.commission_payment import commission_payment_crud, CommissionPaymentCrud
from app.crud import ride_crud, document_crud, user_crud
from app.schemas.commission_payment import CommissionPaymentCreateRequest, CommissionPaymentSchema
from app.services.tbank_acquiring import TBankAPIError, amount_to_minor_units, tbank_acquiring_client
from app.services.webhook_dispatcher import webhook_dispatcher
from app.models import Ride, CommissionPayment
from app.backend.routers.base import BaseRouter
from app.services import pdf_generator
from app.enum import RoleCode
from app.db import async_session_maker


REUSABLE_PAYMENT_STATUSES = {"NEW", "FORM_SHOWED", "AUTHORIZED", "CONFIRMED"}


class CommissionPaymentRouter(BaseRouter[CommissionPaymentCrud]):
    def __init__(self, model_crud: CommissionPaymentCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)
        
    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{id}}/payment-link", self.create_payment_link, methods=["POST"], status_code=201, dependencies=[Depends(require_owner(Ride, "client_id"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_commission_payment, methods=["GET"], status_code=200, dependencies=[Depends(require_owner(CommissionPayment, "user_id"))])

    async def create_payment_link(self, request: Request, id: int, body: CommissionPaymentCreateRequest, user=Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN])), generate_check: bool = False) -> CommissionPaymentSchema:
        session = request.state.session

        ride = await ride_crud.get_by_id(session, id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        existing = await self.model_crud.get_by_ride_and_user(session, id, user.id, is_refund=False)
        if existing and existing.payment_link and existing.status in REUSABLE_PAYMENT_STATUSES:
            return existing

        amount = ride.commission_amount
        if amount is None:
            raise HTTPException(status_code=400, detail="Commission amount is not set")

        purpose = f"Commission for ride #{id}"
        redirect_url = body.redirect_url or TBANK_PAYMENT_REDIRECT_URL
        fail_redirect_url = body.fail_redirect_url or TBANK_PAYMENT_FAIL_REDIRECT_URL
        notification_url = TBANK_PAYMENT_NOTIFICATION_URL
        order_id = f"cp-{id}-{user.id}-{int(datetime.now(timezone.utc).timestamp())}"

        try:
            resp = await tbank_acquiring_client.init_payment(
                amount=float(amount),
                order_id=order_id,
                description=purpose,
                success_url=redirect_url,
                fail_url=fail_redirect_url,
                notification_url=notification_url,
            )
        except TBankAPIError as e:
            raise HTTPException(status_code=502, detail=str(e))

        fields = {
            "ride_id": id,
            "user_id": user.id,
            "amount": amount,
            "currency": "RUB",
            "status": resp.get("Status") or "NEW",
            "payment_id": str(resp.get("PaymentId")) if resp.get("PaymentId") is not None else None,
            "payment_link": resp.get("PaymentURL"),
            "purpose": purpose,
            "payment_mode": list(body.payment_mode),
            "updated_at": datetime.now(timezone.utc),
        }

        async def _generate_and_upload_check(item: CommissionPaymentSchema) -> None:
            key = f"receipts/commissions/{id}/receipt.pdf"
            client = await user_crud.get_by_id(session, item.user_id)
            client_full_name = [word for word in [client.first_name, client.last_name, client.middle_name] if word] if client else []
            payment_mode_value = item.payment_mode
            if isinstance(payment_mode_value, (list, tuple)):
                payment_mode_str = ", ".join([str(x) for x in payment_mode_value])
            else:
                payment_mode_str = str(payment_mode_value) if payment_mode_value is not None else "Карта"

            pdf_bytes = await pdf_generator.generate_commission_receipt(
                ride_id=id,
                client_name=" ".join(client_full_name) or str(item.user_id),
                amount=float(item.amount or 0),
                purpose=item.purpose or purpose,
                payment_mode=payment_mode_str,
                operation_id=item.payment_id or item.tochka_operation_id,
                created_at=getattr(item, "created_at", None),
            )
            await document_crud.upload_bytes(key, pdf_bytes)

        if existing:
            updated = await self.model_crud.update(session, existing.id, fields)
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to update commission payment")
            asyncio.create_task(self._send_sandbox_webhook(updated))
            if generate_check:
                await _generate_and_upload_check(updated)
            return updated

        created = await self.model_crud.create(session, {**fields, "created_at": datetime.now(timezone.utc)})
        asyncio.create_task(self._send_sandbox_webhook(created))
        if generate_check:
            await _generate_and_upload_check(created)
        return created

    async def get_commission_payment(self, request: Request, id: int) -> CommissionPaymentSchema:
        session = request.state.session
        item = await self.model_crud.get_by_id(session, id)
        if not item:
            raise HTTPException(status_code=404, detail="Commission payment not found")
        if item.payment_id and item.status not in {"CONFIRMED", "REJECTED", "AUTH_FAIL", "DEADLINE_EXPIRED", "CANCELED", "CANCELLED"}:
            try:
                await webhook_dispatcher.sync_payment_state(session, item.payment_id)
            except TBankAPIError as e:
                raise HTTPException(status_code=502, detail=str(e))
            refreshed = await self.model_crud.get_by_id(session, id)
            if refreshed:
                return refreshed
        return item

    async def _send_sandbox_webhook(self, item: CommissionPaymentSchema):
        if TBANK_USE_SANDBOX and item.payment_id:
            await asyncio.sleep(3)
            async with async_session_maker() as session:
                await webhook_dispatcher.dispatch_webhook(session, {
                    "TerminalKey": "sandbox-terminal",
                    "OrderId": f"cp-{item.ride_id}-{item.user_id}",
                    "Success": True,
                    "Status": "CONFIRMED",
                    "PaymentId": item.payment_id,
                    "ErrorCode": "0",
                    "Amount": amount_to_minor_units(item.amount),
                }, verify_token=False)
                await session.commit()


commission_payment_router = CommissionPaymentRouter(commission_payment_crud, "/commissions/payments").router
