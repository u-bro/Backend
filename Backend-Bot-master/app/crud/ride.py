from datetime import datetime, timezone
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import insert, update, delete
from app.crud.base import CrudBase
from .tariff_plan import tariff_plan_crud
from .ride_status_history import ride_status_history_crud
from .driver_profile import driver_profile_crud
from app.models import Ride, TariffPlan
from app.schemas.ride import RideSchema
from app.schemas.ride_status_history import RideStatusHistoryCreate
from fastapi import HTTPException


STATUSES = {
    "requested",
    "accepted",
    "started",
    "completed",
    "canceled",
}

ALLOWED_TRANSITIONS = {
    "requested": { "canceled"},
    "accepted": {"started", "canceled"},
    "started": {"completed", "canceled"},
}


class CrudRide(CrudBase):
    @staticmethod
    def _calculate_expected_fare(tariff_plan: TariffPlan, distance_meters: int | None) -> float | None:
        return (float(tariff_plan.base_fare) + (float(distance_meters) * float(tariff_plan.rate_per_meter) * float(tariff_plan.multiplier)))

    @staticmethod
    def _build_snapshot(tariff_plan: TariffPlan, distance_meters: int | None, expected_fare: float | None) -> dict:
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
            "totals": {
                "base_fare": float(tariff_plan.base_fare),
                "rate_per_meter": float(tariff_plan.rate_per_meter),
                "multiplier": float(tariff_plan.multiplier),
                "distance_meters": distance_meters,
                "formula": "base_fare + (distance_meters * rate_per_meter * multiplier))",
                "expected_fare": expected_fare,
            },
            "meta": {
                "calculated_at": _iso_utc_z(datetime.now(timezone.utc)),
            },
        }

    @staticmethod
    def _add_expected_fare_and_snapshot(data: dict, tariff_plan: TariffPlan, distance_meters: int):
        expected_fare = CrudRide._calculate_expected_fare(tariff_plan, distance_meters)
        snapshot = CrudRide._build_snapshot(tariff_plan, distance_meters, expected_fare)
        data["expected_fare"] = expected_fare
        data["expected_fare_snapshot"] = snapshot

    async def create(self, session: AsyncSession, create_obj) -> RideSchema | None:
        data = create_obj.model_dump()
        tariff_plan = await tariff_plan_crud.get_by_id(session, data.get("tariff_plan_id"))

        if not tariff_plan:
            raise HTTPException(status_code=404, detail="Tariff plan not found")
        if tariff_plan.effective_to and tariff_plan.effective_to <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="This version of tariff plan has closed")

        self._add_expected_fare_and_snapshot(data, tariff_plan, data.get("distance_meters"))
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

        should_reprice = any(key in data for key in ("distance_meters", "tariff_plan_id",))
        if should_reprice:
            tariff_plan_id = data.get("tariff_plan_id", existing.tariff_plan_id)
            tariff_plan = await tariff_plan_crud.get_by_id(session, int(tariff_plan_id))
            distance_meters = data.get("distance_meters", existing.distance_meters)
            self._add_expected_fare_and_snapshot(data, tariff_plan, distance_meters)

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

    async def get_requested_rides(self, session: AsyncSession, limit: int = 1) -> list[RideSchema]:
        stmt = select(self.model).where(and_(self.model.status == "requested", self.model.driver_profile_id.is_(None))).limit(limit)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [self.schema.model_validate(ride) for ride in rides]

ride_crud = CrudRide(Ride, RideSchema)
