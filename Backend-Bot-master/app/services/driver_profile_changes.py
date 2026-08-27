from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.const import ACTIVE_RIDE_STATUSES
from app.models import DriverProfile, Ride


PROFILE_UPDATE_FORBIDDEN = "DRIVER_HAS_ACTIVE_RIDE_PROFILE_UPDATE_FORBIDDEN"


async def lock_driver_profile(session: AsyncSession, driver_profile_id: int) -> DriverProfile:
    profile = (
        await session.execute(
            select(DriverProfile)
            .where(DriverProfile.id == driver_profile_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    return profile


async def demoderate_approved_driver(session: AsyncSession, profile: DriverProfile) -> None:
    if not profile.approved:
        return

    active_ride_id = await session.scalar(
        select(Ride.id).where(
            Ride.driver_profile_id == profile.id,
            Ride.status.in_(ACTIVE_RIDE_STATUSES),
        ).limit(1)
    )
    if active_ride_id is not None:
        raise HTTPException(status_code=409, detail=PROFILE_UPDATE_FORBIDDEN)

    profile.approved = False
    profile.status = "waiting_approved"
    profile.approved_by = None
    profile.approved_at = None
    profile.updated_at = datetime.now(timezone.utc)

    # Local imports avoid the driver profile/request CRUD import cycle.
    from app.crud.driver_tracker import DriverStatus, driver_tracker
    from app.crud.ride_drivers_request import ride_drivers_request_crud

    await ride_drivers_request_crud.cancel_by_driver_profile_id(
        session, profile.id, "driver_profile_resubmitted"
    )
    await driver_tracker.set_status_by_driver(session, profile.id, DriverStatus.OFFLINE)
