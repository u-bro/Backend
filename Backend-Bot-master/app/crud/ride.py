from datetime import datetime, timezone
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import insert, update, delete, text
from app.crud.base import CrudBase
from .tariff_plan import tariff_plan_crud
from .commission import commission_crud
from .ride_status_history import ride_status_history_crud
from .driver_profile import driver_profile_crud
from .driver_location import driver_location_crud
from .in_app_notification import in_app_notification_crud
from .driver_tracker import driver_tracker, DriverStatus
from app.models import Ride, TariffPlan, Commission, RideDriversRequest
from app.schemas.ride import RideSchema, RideSchemaHistory
from app.schemas.ride_status_history import RideStatusHistoryCreate
from app.schemas.in_app_notification import InAppNotificationCreate
from fastapi import HTTPException


STATUSES = {
    "requested",
    "waiting_commission",
    "accepted",
    "on_the_way",
    "arrived",
    "started",
    "completed",
    "canceled",
}

ALLOWED_TRANSITIONS = {
    "requested": {"canceled"},
    'waiting_commission': {"accepted", "canceled"},
    "accepted": {"on_the_way", "canceled"},
    'on_the_way': {"arrived", "canceled"},
    'arrived': {"started", "canceled"},
    "started": {"completed", "canceled"},
}


class CrudRide(CrudBase):
    @staticmethod
    def _calculate_expected_fare(tariff_plan: TariffPlan, distance_meters: int | None) -> float | None:
        return (float(tariff_plan.base_fare) + (float(distance_meters) * float(tariff_plan.rate_per_meter) * float(tariff_plan.multiplier)))

    @staticmethod
    def _calculate_commission_amount(expected_fare: float | None, commission: Commission) -> float | None:
        return commission.fixed_amount + (expected_fare * commission.percentage / 100)

    @staticmethod
    def _build_snapshot(tariff_plan: TariffPlan, distance_meters: int | None, expected_fare: float | None, commission: Commission, commission_amount: float | None) -> dict:
        def _iso_utc_z(value: datetime | None) -> str | None:
            if value is None:
                return None
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            value = value.astimezone(timezone.utc)
            return value.isoformat().replace("+00:00", "Z")

        effective_from = getattr(tariff_plan, "effective_from", None)
        effective_to = getattr(tariff_plan, "effective_to", None)
        return {
            "input": {
                "distance_meters": distance_meters,
            },
            "tariff_plan": {
                "id": tariff_plan.id,
                "name": tariff_plan.name,
                "effective_from": _iso_utc_z(effective_from),
                "effective_to": _iso_utc_z(effective_to),
                "rules": getattr(tariff_plan, "rules", None),
            },
            "commission": {
                "id": commission.id,
                "name": commission.name,
                "valid_from": _iso_utc_z(commission.valid_from),
                "valid_to": _iso_utc_z(commission.valid_to)
            },
            "totals": {
                "base_fare": float(tariff_plan.base_fare),
                "rate_per_meter": float(tariff_plan.rate_per_meter),
                "multiplier": float(tariff_plan.multiplier),
                "commission_fixed_amount": commission.fixed_amount,
                "commission_percentage": commission.percentage,
                "distance_meters": distance_meters,
                "expected_fare_formula": "(base_fare + (distance_meters * rate_per_meter * multiplier))",
                "commission_formula": "commission_fixed_amount + (expected_fare * commission_percentage / 100)",
                "expected_fare": expected_fare,
                "commission_amount": commission_amount
            },
            "meta": {
                "calculated_at": _iso_utc_z(datetime.now(timezone.utc)),
            },
        }

    @staticmethod
    def _add_expected_fare_and_snapshot(data: dict, tariff_plan: TariffPlan, distance_meters: int, commission: Commission):
        expected_fare = CrudRide._calculate_expected_fare(tariff_plan, distance_meters)
        commission_amount = CrudRide._calculate_commission_amount(expected_fare, commission)
        snapshot = CrudRide._build_snapshot(tariff_plan, distance_meters, expected_fare, commission, commission_amount)
        data["expected_fare"] = expected_fare
        data["commission_amount"] = commission_amount
        data["expected_fare_snapshot"] = snapshot

    async def create(self, session: AsyncSession, create_obj) -> RideSchema | None:
        data = create_obj.model_dump()
        await self.cancel_rides_by_user_id(session, data.get('client_id'))
        tariff_plan = await tariff_plan_crud.get_by_id(session, data.get("tariff_plan_id"))
        commission = await commission_crud.get_by_id(session,  data.get("commission_id"))

        if not tariff_plan:
            raise HTTPException(status_code=404, detail="Tariff plan not found")
        if tariff_plan.effective_to and tariff_plan.effective_to <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="This version of tariff plan has closed")

        self._add_expected_fare_and_snapshot(data, tariff_plan, data.get("distance_meters"), commission)
        stmt = insert(self.model).values(data).returning(self.model)
        ride = await self.execute_get_one(session, stmt)
        if not ride:
            raise HTTPException(status_code=400, detail="Ride wasn't created")
        await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=ride.id, from_status=None, to_status='requested', changed_by=create_obj.client_id, created_at=datetime.now(timezone.utc)))
        return self.schema.model_validate(ride)

    async def update(self, session: AsyncSession, id: int, update_obj, user_id: int) -> RideSchema | None:
        existing_result = await session.execute(select(self.model).where(self.model.id == id))
        existing = existing_result.scalar_one_or_none()

        data = update_obj.model_dump(exclude_none=True)
        data.pop("expected_fare", None)
        data.pop("expected_fare_snapshot", None)

        should_reprice = any(key in data for key in ("distance_meters", "tariff_plan_id"))
        if should_reprice:
            tariff_plan_id = data.get("tariff_plan_id", existing.tariff_plan_id)
            tariff_plan = await tariff_plan_crud.get_by_id(session, int(tariff_plan_id))
            commission_id = data.get("commission_id", existing.commission_id)
            commission = await commission_crud.get_by_id(session,  int(commission_id))
            distance_meters = data.get("distance_meters", existing.distance_meters)
            self._add_expected_fare_and_snapshot(data, tariff_plan, distance_meters, commission)

        if not data:
            return await self.get_by_id(session, id)

        if update_obj.status and existing.status != update_obj.status:
            if not self._is_status_transition_allowed(existing.status, update_obj.status):
                raise HTTPException(status_code=400, detail="Incorrect ride status transition")
            await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=existing.id, from_status=existing.status, to_status=update_obj.status, changed_by=int(user_id), created_at=datetime.now(timezone.utc)))

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        return self.schema.model_validate(result)

    @staticmethod
    def _is_status_transition_allowed(from_status: str, to_status: str) -> bool:
        if to_status not in STATUSES or to_status not in ALLOWED_TRANSITIONS.get(from_status, []):
            return False

        return True

    async def accept(self, session: AsyncSession, id: int, update_obj, user_id: int) -> RideSchema | None:
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, update_obj.driver_profile_id)
        if not driver_location:
            raise HTTPException(status_code=404, detail="Driver location not found")
        if driver_location.status == 'busy':
            raise HTTPException(status_code=409, detail="Driver already have accepted ride")
        stmt = (
            update(self.model)
            .where(and_(self.model.id == id, self.model.driver_profile_id.is_(None)))
            .values(driver_profile_id=update_obj.driver_profile_id, status=update_obj.status)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=result.id, from_status='requested', to_status=update_obj.status, changed_by=user_id, created_at=datetime.now(timezone.utc)))
        await driver_profile_crud.ride_count_increment(session, update_obj.driver_profile_id)
        return self.schema.model_validate(result)

    async def delete(self, session: AsyncSession, id: int):
        stmt = delete(self.model).where(self.model.id == id).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        await driver_profile_crud.ride_count_decrement(session, result.driver_profile_id)
        return self.schema.model_validate(result)
    
    async def cancel_rides_by_user_id(self, session: AsyncSession, user_id: int):
        stmt = select(self.model).where(and_(self.model.status.in_(["requested", "waiting_commission", "accepted", "on_the_way", "arrived", "started"]), self.model.client_id == user_id))
        result = await session.execute(stmt)
        existing_rides = result.scalars().all()
        if not existing_rides or not len(existing_rides):
            return
        ids = [ride.id for ride in existing_rides]
        driver_profile_ids = [ride.driver_profile_id for ride in existing_rides]

        update_stmt_rides = update(self.model).where(self.model.id.in_(ids)).values(status="canceled")
        await session.execute(update_stmt_rides)

        for id in driver_profile_ids:
            await driver_tracker.release_ride(session, id)
        
        requests = await session.execute(update(RideDriversRequest).where(RideDriversRequest.ride_id.in_(ids)).values(status="rejected").returning(RideDriversRequest))
        for request in requests.scalars().all():
            await driver_tracker.set_status_by_driver(session, request.driver_profile_id, DriverStatus.ONLINE)
        
        ride = self.schema.model_validate(existing_rides[0])
        await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=user_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена, т.к. была создана новая", data=ride.model_dump(mode='json'), dedup_key=f"{ride.id}_canceled"))

    async def get_by_client_id(self, session: AsyncSession, client_id: int, order_by: str | None = None) -> list[RideSchema]:
        stmt = select(self.model).where(self.model.client_id == client_id).order_by(text(order_by) if order_by else None)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [self.schema.model_validate(ride) for ride in rides]

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> list[RideSchema]:
        stmt = select(self.model).where(self.model.driver_profile_id == driver_profile_id)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [self.schema.model_validate(ride) for ride in rides]

    async def get_by_client_id_paginated(self, session: AsyncSession, client_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchemaHistory]:
        offset = (page - 1) * page_size
        stmt = select(self.model).where(self.model.client_id == client_id).order_by(text(order_by) if order_by else None).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchemaHistory.model_validate(ride) for ride in rides]

    async def get_by_driver_profile_id_paginated(self, session: AsyncSession, driver_profile_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchemaHistory]:
        offset = (page - 1) * page_size
        stmt = select(self.model).where(self.model.driver_profile_id == driver_profile_id).order_by(text(order_by) if order_by else None).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchemaHistory.model_validate(ride) for ride in rides]

    async def get_active_ride_by_client_id(self, session: AsyncSession, client_id: int) -> RideSchema | None:
        stmt = select(self.model).where(and_(self.model.client_id == client_id, self.model.status.in_(["requested", "waiting_commission", "accepted", "on_the_way", "arrived", "started"])))
        result = await session.execute(stmt)
        ride = result.scalar_one_or_none()
        return self.schema.model_validate(ride) if ride else None

    async def get_active_ride_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> RideSchema | None:
        result = await session.execute(select(self.model).where(and_(self.model.status.in_(["waiting_commission", "accepted", "on_the_way", "arrived", "started"]), Ride.driver_profile_id == driver_profile_id)))
        ride = result.scalar_one_or_none()
        return self.schema.model_validate(ride) if ride else None

ride_crud = CrudRide(Ride, RideSchema)
