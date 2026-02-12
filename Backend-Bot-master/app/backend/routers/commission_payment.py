from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from app.backend.deps import require_role, require_owner
from app.config import TOCHKA_ACQUIRING_FAIL_REDIRECT_URL, TOCHKA_ACQUIRING_REDIRECT_URL, TOCHKA_USE_SANDBOX, TOCHKA_WEBHOOK_EXAMPLE
from app.crud import ride_crud, commission_payment_crud, document_crud, user_crud
from app.schemas.commission_payment import CommissionPaymentCreateRequest, CommissionPaymentSchema
from app.services.tochka_acquiring import TochkaAPIError, tochka_acquiring_client
from app.services.webhook_dispatcher import webhook_dispatcher
from app.models import Ride, CommissionPayment
from app.backend.routers.base import BaseRouter
from app.services import pdf_generator


class CommissionPaymentRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(commission_payment_crud, "/commissions/payments")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{id}}/payment-link", self.create_payment_link, methods=["POST"], status_code=201, dependencies=[Depends(require_owner(Ride, "client_id"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_owner(CommissionPayment, "user_id"))])

    async def create_payment_link(self, request: Request, id: int, body: CommissionPaymentCreateRequest, user=Depends(require_role(["user", "driver", "admin"])), generate_check: bool = False) -> CommissionPaymentSchema:
        session = request.state.session

        ride = await ride_crud.get_by_id(session, id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        existing = await commission_payment_crud.get_by_ride_and_user(session, id, user.id, is_refund=False)
        if existing and existing.payment_link:
            return existing

        amount = ride.commission_amount
        purpose = f"Commission for ride #{id}"
        redirect_url = body.redirect_url or TOCHKA_ACQUIRING_REDIRECT_URL
        fail_redirect_url = body.fail_redirect_url or TOCHKA_ACQUIRING_FAIL_REDIRECT_URL

        try:
            resp = await tochka_acquiring_client.create_payment_link(
                amount=float(amount),
                purpose=purpose,
                payment_mode=list(body.payment_mode),
                redirect_url=redirect_url,
                fail_redirect_url=fail_redirect_url,
            )
        except TochkaAPIError as e:
            raise HTTPException(status_code=502, detail=str(e))

        data = (resp or {}).get("Data") or {}

        fields = {
            "ride_id": id,
            "user_id": user.id,
            "amount": amount,
            "currency": "RUB",
            "status": data.get("status") or "CREATED",
            "tochka_operation_id": data.get("operationId") if not TOCHKA_USE_SANDBOX else 'beeac8a4-6047-3f38-8922-a664e6b5c43b',
            "payment_link": data.get("paymentLink"),
            "purpose": data.get("purpose") or purpose,
            "payment_mode": data.get("paymentMode") or list(body.payment_mode),
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
                operation_id=item.tochka_operation_id,
                created_at=getattr(item, "created_at", None),
            )
            await document_crud.upload_bytes(key, pdf_bytes)

        if existing:
            updated = await commission_payment_crud.update(session, existing.id, fields)
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to update commission payment")
            if TOCHKA_USE_SANDBOX:
                await webhook_dispatcher.dispatch_webhook(session, TOCHKA_WEBHOOK_EXAMPLE)
            if generate_check:
                await _generate_and_upload_check(updated)
            return updated

        created = await commission_payment_crud.create(session, {**fields, "created_at": datetime.now(timezone.utc)})
        if TOCHKA_USE_SANDBOX:
            await webhook_dispatcher.dispatch_webhook(session, TOCHKA_WEBHOOK_EXAMPLE)
        if generate_check:
            await _generate_and_upload_check(created)
        return created

    async def get_commission_payment(self, request: Request, id: int) -> CommissionPaymentSchema:
        session = request.state.session
        item = await commission_payment_crud.get_by_id(session, id)
        if not item:
            raise HTTPException(status_code=404, detail="Commission payment not found")
        return item


commission_payment_router = CommissionPaymentRouter().router