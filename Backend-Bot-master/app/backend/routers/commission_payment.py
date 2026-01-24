from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from app.backend.deps import require_role, require_owner
from app.config import TOCHKA_ACQUIRING_FAIL_REDIRECT_URL, TOCHKA_ACQUIRING_REDIRECT_URL, TOCHKA_USE_SANDBOX, TOCHKA_WEBHOOK_EXAMPLE
from app.crud import ride_crud, commission_payment_crud
from app.schemas.commission_payment import CommissionPaymentCreateRequest, CommissionPaymentSchema
from app.services.tochka_acquiring import TochkaAPIError, tochka_acquiring_client
from app.services.webhook_dispatcher import webhook_dispatcher
from app.models import Ride, CommissionPayment
from app.backend.routers.base import BaseRouter


class CommissionPaymentRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(commission_payment_crud, "/commissions/payments")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{id}}/payment-link", self.create_payment_link, methods=["POST"], status_code=201, dependencies=[Depends(require_owner(Ride, "client_id"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_owner(CommissionPayment, "user_id"))])

    async def create_payment_link(self, request: Request, id: int, body: CommissionPaymentCreateRequest, user=Depends(require_role(["user", "driver", "admin"]))) -> CommissionPaymentSchema:
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
        raw_request = {
            "amount": float(amount),
            "purpose": purpose,
            "paymentMode": body.payment_mode,
            "redirectUrl": redirect_url,
            "failRedirectUrl": fail_redirect_url,
        }

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
            "raw_request": raw_request,
            "raw_response": resp,
            "updated_at": datetime.now(timezone.utc),
        }

        if existing:
            updated = await commission_payment_crud.update(session, existing.id, fields)
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to update commission payment")
            if TOCHKA_USE_SANDBOX:
                await webhook_dispatcher.dispatch_webhook(session, TOCHKA_WEBHOOK_EXAMPLE)
            return updated

        created = await commission_payment_crud.create(session, {**fields, "created_at": datetime.now(timezone.utc)})
        if TOCHKA_USE_SANDBOX:
            await webhook_dispatcher.dispatch_webhook(session, TOCHKA_WEBHOOK_EXAMPLE)
        return created

    async def get_commission_payment(self, request: Request, id: int) -> CommissionPaymentSchema:
        session = request.state.session
        item = await commission_payment_crud.get_by_id(session, id)
        if not item:
            raise HTTPException(status_code=404, detail="Commission payment not found")
        return item


commission_payment_router = CommissionPaymentRouter().router