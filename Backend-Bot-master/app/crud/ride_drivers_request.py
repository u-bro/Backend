from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import DRIVER_PENDING_REQUEST_LIMIT
from app.const import ACTIVE_RIDE_STATUSES
from app.crud.base import CrudBase
from app.models import DriverProfile, Ride, RideDriversRequest
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from app.schemas.ride import RideSchemaAcceptByDriver
from app.schemas.ride_drivers_request import (
    RideDriversRequestCreate,
    RideDriversRequestSchema,
    RideDriversRequestSchemaDetailed,
    RideDriversRequestSchemaWithRide,
    RideDriversRequestUpdate,
)
from app.services import fcm_service
from app.services.after_commit import add_after_commit
from app.services.websocket_manager import manager_driver_feed

from .commission import commission_crud
from .commission_payment import commission_payment_crud
from .driver_profile import driver_profile_crud
from .driver_location import driver_location_crud
from .driver_tracker import DriverStatus, driver_tracker
from .in_app_notification import in_app_notification_crud
from .ride import ride_crud


class RideDriversRequestCrud(CrudBase[RideDriversRequest, RideDriversRequestSchema]):
    def __init__(self) -> None:
        super().__init__(RideDriversRequest, RideDriversRequestSchema)

    async def get_by_ride_id(self, session: AsyncSession, ride_id: int) -> list[RideDriversRequestSchema]:
        result = await session.execute(select(self.model).where(self.model.ride_id == ride_id))
        return [self.schema.model_validate(item) for item in result.scalars().all()]

    async def get_accepted_by_ride_id(self, session: AsyncSession, ride_id: int) -> RideDriversRequestSchema | None:
        result = await session.execute(select(self.model).where(self.model.ride_id == ride_id, self.model.status == "accepted"))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def get_by_ride_id_detailed(self, session: AsyncSession, ride_id: int) -> list[RideDriversRequestSchemaDetailed]:
        result = await session.execute(select(self.model).options(joinedload(self.model.driver_profile), joinedload(self.model.car)).where(self.model.ride_id == ride_id))
        return [RideDriversRequestSchemaDetailed.model_validate(item) for item in result.scalars().all()]

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> list[RideDriversRequestSchema]:
        result = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        return [self.schema.model_validate(item) for item in result.scalars().all()]

    async def get_requested_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, limit: int = DRIVER_PENDING_REQUEST_LIMIT) -> list[RideDriversRequestSchema]:
        result = await session.execute(
            select(self.model)
            .where(self.model.driver_profile_id == driver_profile_id, self.model.status == "requested")
            .order_by(self.model.created_at.desc(), self.model.id.desc())
            .limit(limit)
        )
        return [self.schema.model_validate(item) for item in result.scalars().all()]

    async def get_requested_with_ride_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, limit: int = DRIVER_PENDING_REQUEST_LIMIT) -> list[RideDriversRequestSchemaWithRide]:
        result = await session.execute(
            select(self.model)
            .options(joinedload(self.model.ride))
            .where(self.model.driver_profile_id == driver_profile_id, self.model.status == "requested")
            .order_by(self.model.created_at.desc(), self.model.id.desc())
            .limit(limit)
        )
        return [RideDriversRequestSchemaWithRide.model_validate(item) for item in result.scalars().all()]

    async def get_requested_by_ride_id_and_driver_profile_id(self, session: AsyncSession, ride_id: int, driver_profile_id: int) -> RideDriversRequestSchema | None:
        result = await session.execute(select(self.model).where(self.model.ride_id == ride_id, self.model.driver_profile_id == driver_profile_id, self.model.status == "requested"))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def create(self, session: AsyncSession, create_obj: RideDriversRequestCreate) -> RideDriversRequestSchema:
        # Locks serialize count checks and active-ride checks for one driver.
        driver = (await session.execute(select(DriverProfile).where(DriverProfile.id == create_obj.driver_profile_id).with_for_update())).scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        if not driver.approved or driver.status != "approved":
            raise HTTPException(status_code=403, detail="DRIVER_NOT_APPROVED")

        active_ride = await session.scalar(select(Ride.id).where(Ride.driver_profile_id == create_obj.driver_profile_id, Ride.status.in_(ACTIVE_RIDE_STATUSES)).limit(1))
        if active_ride:
            raise HTTPException(status_code=409, detail="DRIVER_ALREADY_ASSIGNED")

        ride = (await session.execute(select(Ride).where(Ride.id == create_obj.ride_id).with_for_update())).scalar_one_or_none()
        if not ride:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        if ride.status != "requested" or ride.driver_profile_id is not None:
            raise HTTPException(status_code=409, detail="RIDE_ALREADY_ASSIGNED")
        if ride.ride_type == "with_car" and not create_obj.car_id:
            raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

        pending_count = await session.scalar(select(func.count()).select_from(self.model).where(self.model.driver_profile_id == create_obj.driver_profile_id, self.model.status == "requested"))
        if pending_count >= DRIVER_PENDING_REQUEST_LIMIT:
            raise HTTPException(status_code=409, detail="DRIVER_PENDING_REQUEST_LIMIT")

        commission = await commission_crud.get_by_id(session, ride.commission_id)
        if not commission:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        values = create_obj.model_dump()
        values["commission_amount"] = ride_crud._calculate_commission_amount(create_obj.offer_fare, commission)
        stmt = insert(self.model).values(values).on_conflict_do_nothing(index_elements=[self.model.ride_id, self.model.driver_profile_id], index_where=self.model.status == "requested").returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if not result:
            raise HTTPException(status_code=409, detail="RIDE_REQUEST_ALREADY_EXISTS")

        await driver_tracker.set_status_by_driver(session, result.driver_profile_id, DriverStatus.WAITING_RIDE)
        notification = InAppNotificationCreate(user_id=ride.client_id, type="ride_offer", title="Новый отклик", message="На поездку откликнулся ещё один водитель", data={"offer_id": result.id, "ride_id": result.ride_id, "driver_profile_id": result.driver_profile_id}, dedup_key=f"ride_request:{result.id}:created")
        await in_app_notification_crud.create(session, notification)
        add_after_commit(session, lambda client_id=ride.client_id, title=notification.title, message=notification.message: fcm_service.send_to_user_after_commit(client_id, PushNotificationData(title=title, body=message)))
        return self.schema.model_validate(result)

    async def update(self, session: AsyncSession, id: int, update_obj: RideDriversRequestUpdate) -> RideDriversRequestSchema:
        request_row = (await session.execute(select(self.model).where(self.model.id == id))).scalar_one_or_none()
        if not request_row:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        if request_row.status != "requested":
            raise HTTPException(status_code=409, detail="RIDE_REQUEST_NOT_PENDING")
        if update_obj.status == "accepted":
            # All acceptances use one transaction-scoped lock, preventing cycles
            # between cross-linked ride/driver request sets.
            await session.execute(text("SELECT pg_advisory_xact_lock(7269433101)"))
            await session.execute(select(DriverProfile.id).where(DriverProfile.id == request_row.driver_profile_id).with_for_update())
            await session.execute(select(Ride.id).where(Ride.id == request_row.ride_id).with_for_update())
            request_row = (await session.execute(select(self.model).where(self.model.id == id).with_for_update())).scalar_one()
            if request_row.status != "requested":
                raise HTTPException(status_code=409, detail="RIDE_REQUEST_NOT_PENDING")
            try:
                async with session.begin_nested():
                    accepted = await self._accept(session, request_row, update_obj)
                return accepted
            except IntegrityError as exc:
                constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                if constraint == "uq_rides_one_active_per_driver":
                    raise HTTPException(status_code=409, detail="DRIVER_ALREADY_ASSIGNED") from exc
                if constraint == "uq_ride_requests_pending_pair":
                    raise HTTPException(status_code=409, detail="RIDE_REQUEST_ALREADY_EXISTS") from exc
                raise
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    async def withdraw(self, session: AsyncSession, id: int) -> RideDriversRequestSchema:
        request_row = (await session.execute(select(self.model).where(self.model.id == id).with_for_update())).scalar_one_or_none()
        if not request_row:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        if request_row.status != "requested":
            raise HTTPException(status_code=409, detail="RIDE_REQUEST_NOT_PENDING")
        return (await self._remove(session, [request_row], "canceled", "driver_withdrawn"))[0]

    async def _accept(self, session: AsyncSession, request_row: RideDriversRequest, update_obj: RideDriversRequestUpdate) -> RideDriversRequestSchema:
        active_ride = await session.scalar(select(Ride.id).where(Ride.driver_profile_id == request_row.driver_profile_id, Ride.status.in_(ACTIVE_RIDE_STATUSES)).limit(1))
        if active_ride:
            raise HTTPException(status_code=409, detail="DRIVER_ALREADY_ASSIGNED")
        ride = (await session.execute(select(Ride).where(Ride.id == request_row.ride_id))).scalar_one_or_none()
        accepted = await ride_crud.accept(session, request_row.ride_id, RideSchemaAcceptByDriver(driver_profile_id=request_row.driver_profile_id, offer_fare=request_row.offer_fare), ride.client_id)
        if not accepted:
            raise HTTPException(status_code=409, detail="RIDE_ALREADY_ASSIGNED")
        request_row.status = "accepted"
        request_row.updated_at = update_obj.updated_at
        await session.flush()
        await driver_tracker.assign_ride(session, request_row.driver_profile_id, accepted.id)

        competitors = (await session.execute(select(self.model).where(self.model.ride_id == request_row.ride_id, self.model.status == "requested", self.model.id != request_row.id).order_by(self.model.id).with_for_update())).scalars().all()
        await self._remove(session, competitors, "rejected", "selected_other_driver")
        other_driver_requests = (await session.execute(select(self.model).where(self.model.driver_profile_id == request_row.driver_profile_id, self.model.status == "requested").order_by(self.model.id).with_for_update())).scalars().all()
        await self._remove(session, other_driver_requests, "canceled", "driver_assigned_elsewhere")

        driver = await driver_profile_crud.get_by_id(session, request_row.driver_profile_id)
        accepted_payload = accepted.model_dump(mode="json")
        add_after_commit(session, lambda driver_id=driver.user_id, accepted_payload=accepted_payload: manager_driver_feed.send_personal_message(driver_id, {"type": "ride_status_changed", "data": accepted_payload, "meta": {"previous_status": "requested", "actor": "client", "reason": "driver_selected"}}))
        add_after_commit(session, lambda: _start_background_task(commission_payment_crud.cancel_commission_payment_if_timeout(request_row.ride_id, ride.client_id)))
        return self.schema.model_validate(request_row)

    async def _remove(self, session: AsyncSession, rows: list[RideDriversRequest], status: str, reason: str) -> list[RideDriversRequestSchema]:
        changed = []
        updated_at = datetime.now(timezone.utc)
        for row in rows:
            row.status = status
            row.removal_reason = reason
            row.updated_at = updated_at
            changed.append(self.schema.model_validate(row))
            driver = await driver_profile_crud.get_by_id(session, row.driver_profile_id)
            payload = {
                "type": "ride_request_removed",
                "request_id": row.id,
                "ride_id": row.ride_id,
                "status": status,
                "removal_reason": reason,
            }
            payload["data"] = {
                "request_id": row.id,
                "ride_id": row.ride_id,
                "status": status,
                "removal_reason": reason,
            }
            if driver:
                add_after_commit(session, lambda driver=driver, payload=payload: manager_driver_feed.send_personal_message(driver.user_id, payload))
            if reason in ("driver_withdrawn", "driver_offline"):
                ride = await ride_crud.get_by_id(session, row.ride_id)
                if ride:
                    await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=ride.client_id, type="ride_request_canceled", title="Отклик на поездку отозван", message="Отклик на поездку отозван водителем", data=changed[-1].model_dump(mode="json"), dedup_key=f"ride_request:{row.id}:removed:{reason}"))
            elif reason in ("selected_other_driver", "ride_canceled", "ride_expired") and driver:
                title, message = {
                    "selected_other_driver": ("Выбран другой водитель", "Клиент выбрал другого исполнителя"),
                    "ride_canceled": ("Заказ отменен", "Клиент отменил заказ"),
                    "ride_expired": ("Заказ завершил поиск", "Время поиска исполнителя истекло"),
                }[reason]
                notification = await in_app_notification_crud.create(
                    session,
                    InAppNotificationCreate(
                        user_id=driver.user_id,
                        type="ride_request_removed",
                        title=title,
                        message=message,
                        data=payload,
                        dedup_key=f"ride_request_removed:{row.id}:{status}:{reason}",
                    ),
                )
                if notification is not None:
                    add_after_commit(
                        session,
                        lambda driver=driver, title=title, message=message, payload=payload: fcm_service.send_to_user(
                            session,
                            driver.user_id,
                            PushNotificationData(title=title, body=message, data=payload),
                        ),
                    )
        await session.flush()
        for driver_id in {row.driver_profile_id for row in rows}:
            active = await session.scalar(select(Ride.id).where(Ride.driver_profile_id == driver_id, Ride.status.in_(ACTIVE_RIDE_STATUSES)).limit(1))
            pending = await session.scalar(select(self.model.id).where(self.model.driver_profile_id == driver_id, self.model.status == "requested").limit(1))
            if not active and reason != "driver_offline":
                location = await driver_location_crud.get_by_driver_profile_id(session, driver_id)
                status = DriverStatus.OFFLINE if location and location.status == DriverStatus.OFFLINE else DriverStatus.WAITING_RIDE if pending else DriverStatus.ONLINE
                await driver_tracker.set_status_by_driver(session, driver_id, status)
        return changed

    async def reject_by_ride_id(self, session: AsyncSession, ride_id: int, reason: str = "ride_canceled") -> None:
        rows = (await session.execute(select(self.model).where(self.model.ride_id == ride_id, self.model.status == "requested").order_by(self.model.id).with_for_update())).scalars().all()
        status = "rejected" if reason == "selected_other_driver" else "canceled"
        await self._remove(session, rows, status, reason)

    async def cancel_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, reason: str = "driver_offline") -> None:
        rows = (await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id, self.model.status == "requested").order_by(self.model.id).with_for_update())).scalars().all()
        await self._remove(session, rows, "canceled", reason)


ride_drivers_request_crud = RideDriversRequestCrud()


def _start_background_task(coroutine) -> None:
    import asyncio

    asyncio.create_task(coroutine)
