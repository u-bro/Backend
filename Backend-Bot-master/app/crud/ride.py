from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text
from app.crud.base import CrudBase
from app.models.ride import Ride
from app.models.ride_status_history import RideStatusHistory
from app.schemas.ride import RideSchema, RideCreate, RideUpdate, RideStatusChangeRequest


def _convert_decimals(d: dict) -> dict:
    for k, v in d.items():
        if isinstance(v, Decimal):
            d[k] = float(v)
    return d


STATUSES = {
    "requested",
    "driver_assigned",
    "accepted",
    "arrived",
    "started",
    "completed",
    "canceled",
}

ALLOWED_TRANSITIONS = {
    "client": {
        "requested": {"canceled"},
        "driver_assigned": {"canceled"},
        "accepted": {"canceled"},
    },
    "driver": {
        "driver_assigned": {"accepted", "canceled"},
        "accepted": {"arrived", "canceled"},
        "arrived": {"started", "canceled"},
        "started": {"completed", "canceled"},
    },
    "system": {
        "requested": {"driver_assigned", "canceled"},
        "driver_assigned": {"accepted", "canceled"},
        "accepted": {"arrived", "canceled"},
        "arrived": {"started", "canceled"},
        "started": {"completed", "canceled"},
    },
}


class RideCrud(CrudBase[Ride, RideSchema]):
    def __init__(self) -> None:
        super().__init__(Ride, RideSchema)

    def _strip_timezone(self, values: dict) -> dict:
        datetime_fields = ['scheduled_at', 'started_at', 'completed_at', 'canceled_at']
        for field in datetime_fields:
            if field in values and values[field] is not None:
                dt = values[field]
                if isinstance(dt, datetime) and dt.tzinfo is not None:
                    values[field] = dt.replace(tzinfo=None)
        return values

    async def create(self, session: AsyncSession, create_obj: RideCreate) -> RideSchema | None:
        values = create_obj.model_dump()
        values = self._strip_timezone(values)
        values.setdefault("status", "requested")
        stmt = insert(Ride).values(values).returning(Ride)
        res = await session.execute(stmt)
        ride = res.scalar_one_or_none()
        if not ride:
            return None
        hist = insert(RideStatusHistory).values(
            ride_id=ride.id,
            from_status=None,
            to_status="requested",
            changed_by=create_obj.client_id,
            actor_role="client",
            reason=None,
            meta=None,
            created_at=datetime.utcnow(),
        )
        await session.execute(hist)
        return RideSchema.model_validate(ride)

    async def update(self, session: AsyncSession, id: int, update_obj: RideUpdate) -> RideSchema | None:
        stmt = update(Ride).where(Ride.id == id).values(update_obj.model_dump(exclude_none=True)).returning(Ride)
        res = await session.execute(stmt)
        ride = res.scalar_one_or_none()
        return RideSchema.model_validate(ride) if ride else None

    async def change_status(
        self,
        session: AsyncSession,
        ride_id: int,
        req: RideStatusChangeRequest,
    ) -> RideSchema:
        to_status = req.to_status
        role = req.actor_role
        if to_status not in STATUSES:
            raise ValueError("invalid status")

        role_map = ALLOWED_TRANSITIONS.get(role, {})
        allowed_from = [from_s for from_s, tos in role_map.items() if to_status in tos]
        if not allowed_from:
            raise ValueError("status transition not allowed for this role")

        sql = text(
            """
            WITH prev AS (
                SELECT status AS from_status
                FROM rides
                WHERE id = :ride_id
                FOR UPDATE
            ),
            upd AS (
                UPDATE rides r
                SET
                    status = CAST(:to_status AS VARCHAR),
                    status_reason = :reason,
                    started_at = CASE WHEN CAST(:to_status AS VARCHAR) = 'started' THEN NOW() ELSE r.started_at END,
                    completed_at = CASE WHEN CAST(:to_status AS VARCHAR) = 'completed' THEN NOW() ELSE r.completed_at END,
                    canceled_at = CASE WHEN CAST(:to_status AS VARCHAR) = 'canceled' THEN NOW() ELSE r.canceled_at END,
                    cancellation_reason = CASE WHEN CAST(:to_status AS VARCHAR) = 'canceled' THEN :reason ELSE r.cancellation_reason END,
                    updated_at = NOW()
                WHERE r.id = :ride_id
                  AND (SELECT from_status FROM prev) = ANY(CAST(:allowed_from AS VARCHAR[]))
                RETURNING r.id, r.client_id, r.driver_profile_id, r.status, r.status_reason, r.scheduled_at,
                          r.started_at, r.completed_at, r.canceled_at, r.cancellation_reason,
                          r.pickup_address, r.pickup_lat, r.pickup_lng,
                          r.dropoff_address, r.dropoff_lat, r.dropoff_lng,
                          r.expected_fare, r.expected_fare_snapshot, r.driver_fare, r.actual_fare,
                          r.distance_meters, r.duration_seconds, r.transaction_id, r.commission_id,
                          r.is_anomaly, r.anomaly_reason, r.ride_metadata, r.created_at, r.updated_at
            ),
            ins AS (
                INSERT INTO ride_status_history (
                    ride_id, from_status, to_status, changed_by, actor_role, reason, meta, created_at
                )
                SELECT :ride_id,
                       (SELECT from_status FROM prev),
                       CAST(:to_status AS VARCHAR),
                       :actor_id,
                       CAST(:actor_role AS VARCHAR),
                       :reason,
                       CAST(:meta AS JSONB),
                       NOW()
                WHERE EXISTS (SELECT 1 FROM upd)
                RETURNING 1
            )
            SELECT * FROM upd
            """
        )

        params: dict[str, Any] = {
            "ride_id": ride_id,
            "to_status": to_status,
            "reason": req.reason,
            "actor_id": req.actor_id,
            "actor_role": role,
            "meta": json.dumps(req.meta if req.meta is not None else {}),
            "allowed_from": allowed_from,
        }

        res = await session.execute(sql, params)
        row = res.first()
        if not row:
            raise ValueError("ride not found or status transition not allowed")

        col_names = [
            "id", "client_id", "driver_profile_id", "status", "status_reason",
            "pickup_address", "pickup_lat", "pickup_lng",
            "dropoff_address", "dropoff_lat", "dropoff_lng",
            "scheduled_at", "started_at", "completed_at", "canceled_at", "cancellation_reason",
            "expected_fare", "expected_fare_snapshot", "driver_fare", "actual_fare",
            "distance_meters", "duration_seconds", "transaction_id", "commission_id",
            "is_anomaly", "anomaly_reason", "ride_metadata", "created_at", "updated_at",
        ]
        ride_dict = {k: v for k, v in zip(col_names, row)}
        ride_dict = _convert_decimals(ride_dict)
        return RideSchema.model_validate(ride_dict)

    async def accept_ride_idempotent(
        self,
        session: AsyncSession,
        ride_id: int,
        driver_profile_id: int,
        actor_id: int,
    ) -> tuple[RideSchema | None, str]:
        sql = text(
            """
            WITH current AS (
                SELECT id, status, driver_profile_id
                FROM rides
                WHERE id = :ride_id
                FOR UPDATE NOWAIT
            ),
            upd AS (
                UPDATE rides r
                SET
                    driver_profile_id = :driver_profile_id,
                    status = 'accepted',
                    status_reason = 'Driver accepted',
                    updated_at = NOW()
                WHERE r.id = :ride_id
                  AND r.status IN ('requested', 'driver_assigned')
                  AND (r.driver_profile_id IS NULL OR r.driver_profile_id = :driver_profile_id)
                RETURNING r.*
            ),
            ins AS (
                INSERT INTO ride_status_history (
                    ride_id, from_status, to_status, changed_by, actor_role, reason, meta, created_at
                )
                SELECT :ride_id,
                       (SELECT status FROM current),
                       'accepted',
                       :actor_id,
                       'driver',
                       'Driver accepted ride',
                       '{}',
                       NOW()
                WHERE EXISTS (SELECT 1 FROM upd)
                RETURNING 1
            )
            SELECT 
                upd.*,
                current.status AS prev_status,
                current.driver_profile_id AS prev_driver_id
            FROM current
            LEFT JOIN upd ON true
            """
        )

        params = {
            "ride_id": ride_id,
            "driver_profile_id": driver_profile_id,
            "actor_id": actor_id,
        }

        try:
            res = await session.execute(sql, params)
            row = res.first()
        except Exception as e:
            if "could not obtain lock" in str(e).lower():
                return None, "already_taken"
            raise

        if not row:
            return None, "not_found"

        # Проверяем результат
        prev_status = row[-2]
        prev_driver_id = row[-1]
        

        if row[0] is None:
            if prev_driver_id == driver_profile_id:
                ride = await self.get_by_id(session, ride_id)
                return ride, "already_yours"
            elif prev_driver_id is not None:
                return None, "already_taken"
            elif prev_status not in ('requested', 'driver_assigned'):
                return None, "invalid_status"
            else:
                return None, "already_taken"
        col_names = [
            "id", "client_id", "driver_profile_id", "status", "status_reason",
            "pickup_address", "pickup_lat", "pickup_lng",
            "dropoff_address", "dropoff_lat", "dropoff_lng",
            "scheduled_at", "started_at", "completed_at", "canceled_at", "cancellation_reason",
            "expected_fare", "expected_fare_snapshot", "driver_fare", "actual_fare",
            "distance_meters", "duration_seconds", "transaction_id", "commission_id",
            "is_anomaly", "anomaly_reason", "ride_metadata", "created_at", "updated_at",
        ]
        ride_dict = {k: v for k, v in zip(col_names, row[:-2])}
        ride_dict = _convert_decimals(ride_dict)
        return RideSchema.model_validate(ride_dict), "accepted"

    async def get_pending_rides(
        self,
        session: AsyncSession,
        limit: int = 50,
        ride_class: str | None = None,
    ) -> list[RideSchema]:
        query = select(Ride).where(
            Ride.status.in_(["requested", "driver_assigned"])
        ).order_by(Ride.created_at.desc()).limit(limit)
        
        res = await session.execute(query)
        rides = res.scalars().all()
        return [RideSchema.model_validate(r) for r in rides]


ride_crud = RideCrud()
