from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import exists, func, select

import app.config
from app.crud.driver_feed import driver_feed
from app.crud.in_app_notification import in_app_notification_crud
from app.db import async_session_maker
from app.models import DriverLocation, DriverProfile, Ride, RideDriversRequest
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from app.services.fcm_service import fcm_service


logger = logging.getLogger(__name__)
from app.const import ACTIVE_RIDE_STATUSES
from app.services.after_commit import add_after_commit, commit_with_callbacks, rollback_with_callbacks


def is_matching_driver(driver_location: Any, driver_profile: Any, ride: Any) -> bool:
    """Return whether a persisted driver matches the current feed rules."""
    if driver_location.status not in ("online", "waiting_ride"):
        return False
    if driver_location.latitude is None or driver_location.longitude is None:
        return False

    allowed_classes = {
        str(ride_class).lower()
        for ride_class in (driver_profile.classes_allowed or [])
    }
    if str(ride.ride_class).lower() not in allowed_classes:
        return False

    if ride.ride_type == "with_car" and driver_profile.current_car_id is None:
        return False

    distance = driver_feed._haversine_distance(
        float(driver_location.latitude),
        float(driver_location.longitude),
        float(ride.pickup_lat),
        float(ride.pickup_lng),
    )
    return distance <= app.config.MAX_DISTANCE_KM


def build_new_ride_push_data(ride: Any, distance_to_pickup_km: float) -> dict[str, str]:
    return {
        "type": "new_ride",
        "action": "matching_feed",
        "ride_id": str(ride.id),
        "pickup_lat": str(ride.pickup_lat),
        "pickup_lng": str(ride.pickup_lng),
        "distance_to_pickup_km": str(round(distance_to_pickup_km, 2)),
    }


def _build_notification_message(ride: Any, distance_to_pickup_km: float) -> tuple[str, str]:
    title = "Новый заказ рядом"
    pickup_address = ride.pickup_address or "Точка подачи не указана"
    body = f"{pickup_address} ({distance_to_pickup_km:.2f} км)"
    return title, body[:255]


async def notify_about_new_ride(ride_id: int) -> None:
    """Best-effort notification fan-out for an already-created requested ride."""
    async with async_session_maker() as session:
        try:
            ride_result = await session.execute(
                select(Ride).where(
                    Ride.id == ride_id,
                    Ride.status == "requested",
                    Ride.driver_profile_id.is_(None),
                )
            )
            ride = ride_result.scalar_one_or_none()
            if not ride:
                return

            active_ride_exists = exists(
                select(Ride.id).where(
                    Ride.driver_profile_id == DriverProfile.id,
                    Ride.status.in_(ACTIVE_RIDE_STATUSES),
                )
            )
            pending_count = (
                select(func.count(RideDriversRequest.id))
                .where(
                    RideDriversRequest.driver_profile_id == DriverProfile.id,
                    RideDriversRequest.status == "requested",
                )
                .correlate(DriverProfile)
                .scalar_subquery()
            )
            candidates_result = await session.execute(
                select(DriverLocation, DriverProfile)
                .join(DriverProfile, DriverProfile.id == DriverLocation.driver_profile_id)
                .where(
                    DriverProfile.approved.is_(True),
                    DriverProfile.user_id.is_not(None),
                    DriverLocation.status.in_(("online", "waiting_ride")),
                    DriverLocation.latitude.is_not(None),
                    DriverLocation.longitude.is_not(None),
                    ~active_ride_exists,
                    pending_count < app.config.DRIVER_PENDING_REQUEST_LIMIT,
                )
            )

            for driver_location, driver_profile in candidates_result.all():
                if not is_matching_driver(driver_location, driver_profile, ride):
                    continue

                distance = driver_feed._haversine_distance(
                    float(driver_location.latitude),
                    float(driver_location.longitude),
                    float(ride.pickup_lat),
                    float(ride.pickup_lng),
                )
                title, body = _build_notification_message(ride, distance)
                data = build_new_ride_push_data(ride, distance)
                try:
                    async with session.begin_nested():
                        notification = await in_app_notification_crud.create(
                            session,
                            InAppNotificationCreate(
                                user_id=driver_profile.user_id,
                                type="new_ride",
                                title=title,
                                message=body,
                                data={**data, "pickup_address": ride.pickup_address},
                                dedup_key=f"new_ride:{ride.id}:{driver_profile.id}",
                            ),
                        )
                except Exception:
                    logger.exception(
                        "Failed to save new ride notification ride_id=%s user_id=%s",
                        ride.id,
                        driver_profile.user_id,
                    )
                    continue

                if notification is None:
                    continue

                add_after_commit(
                    session,
                    lambda user_id=driver_profile.user_id, title=title, body=body, data=data: fcm_service.send_to_user_after_commit(
                        user_id,
                        PushNotificationData(title=title, body=body, data=data),
                    ),
                )

            await commit_with_callbacks(session)
        except Exception:
            await rollback_with_callbacks(session)
            logger.exception("New ride notification task failed ride_id=%s", ride_id)
