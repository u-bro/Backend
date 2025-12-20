from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_
from decimal import Decimal
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import insert, update

from app.crud.base import CrudBase
from app.models import Ride, TariffPlan
from app.schemas.ride import RideSchema


class CrudRide(CrudBase):
    async def _get_tariff_plan(self, session: AsyncSession, tariff_plan_id: int) -> TariffPlan:
        result = await session.execute(
            select(TariffPlan).where(
                TariffPlan.id == tariff_plan_id
            )
        )
        tariff_plan = result.scalar_one_or_none()
        if tariff_plan is None:
            raise HTTPException(status_code=400, detail="Tariff plan not found or not active")
        return tariff_plan

    @staticmethod
    def _calculate_expected_fare(*, tariff_plan: TariffPlan, distance_meters: int | None) -> float | None:
        if distance_meters is None:
            return None
        expected = (float(tariff_plan.base_fare) + (float(distance_meters) * float(tariff_plan.rate_per_meter) * float(tariff_plan.multiplier))) * (1 + float(tariff_plan.commission_percentage) / 100)
        return expected

    @staticmethod
    def _build_snapshot(*, tariff_plan: TariffPlan, distance_meters: int | None, duration_seconds: int | None, expected_fare: float | None) -> dict:
        effective_from = getattr(tariff_plan, "effective_from", None)
        effective_to = getattr(tariff_plan, "effective_to", None)
        return {
            "input": {
                "distance_meters": distance_meters,
            },
            "tariff_plan": {
                "id": tariff_plan.id,
                "name": tariff_plan.name,
                "effective_from": effective_from.isoformat() + "Z" if effective_from else None,
                "effective_to": effective_to.isoformat() + "Z" if effective_to else None,
                "rules": getattr(tariff_plan, "rules", None),
            },
            "totals": {
                "base_fare": float(tariff_plan.base_fare),
                "rate_per_meter": float(tariff_plan.rate_per_meter),
                "multiplier": float(tariff_plan.multiplier),
                "distance_meters": distance_meters,
                "commission_percentage": float(tariff_plan.commission_percentage),
                "formula": "base_fare + (distance_meters * rate_per_meter * multiplier)) * (1 + commission_percentage / 100)",
                "expected_fare": expected_fare,
            },
            "meta": {
                "calculated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    async def create(self, session: AsyncSession, create_obj) -> RideSchema | None:
        data = create_obj.model_dump()
        tariff_plan = await self._get_tariff_plan(session, data.get("tariff_plan_id"))
        expected_fare = self._calculate_expected_fare(tariff_plan=tariff_plan, distance_meters=data.get("distance_meters"),)
        snapshot = self._build_snapshot(tariff_plan=tariff_plan, distance_meters=data.get("distance_meters"), duration_seconds=data.get("duration_seconds"), expected_fare=expected_fare)
        data["expected_fare"] = expected_fare
        data["expected_fare_snapshot"] = snapshot

        stmt = insert(self.model).values(data).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def update(self, session: AsyncSession, id: int, update_obj) -> RideSchema | None:
        existing_result = await session.execute(select(self.model).where(self.model.id == id))
        existing: Ride | None = existing_result.scalar_one_or_none()
        if existing is None:
            return None

        data = update_obj.model_dump(exclude_none=True)
        data.pop("expected_fare", None)
        data.pop("expected_fare_snapshot", None)

        should_reprice = any(
            key in data
            for key in (
                "distance_meters",
                "tariff_plan_id",
            )
        )
        if should_reprice:
            tariff_plan_id = data.get("tariff_plan_id", existing.tariff_plan_id)
            tariff_plan = await self._get_tariff_plan(session, int(tariff_plan_id))
            distance_meters = data.get("distance_meters", existing.distance_meters)
            duration_seconds = data.get("duration_seconds", existing.duration_seconds)

            expected_fare = self._calculate_expected_fare(
                tariff_plan=tariff_plan,
                distance_meters=distance_meters,
            )
            snapshot = self._build_snapshot(
                tariff_plan=tariff_plan,
                distance_meters=distance_meters,
                duration_seconds=duration_seconds,
                expected_fare=expected_fare,
            )
            data["expected_fare"] = expected_fare
            data["expected_fare_snapshot"] = snapshot

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def accept(self, session: AsyncSession, id: int, update_obj) -> RideSchema | None:
        stmt = (
            update(self.model)
            .where(and_(self.model.id == id, self.model.driver_profile_id.is_(None)))
            .values(driver_profile_id=update_obj.driver_profile_id, status=update_obj.status)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

ride_crud = CrudRide(Ride, RideSchema)
