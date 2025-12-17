from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.backend.deps.get_current_user import get_current_user
from app.models import DriverLocation, DriverProfile, User


async def require_driver_location_owner(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> DriverLocation:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(
        select(DriverLocation)
        .options(selectinload(DriverLocation.driver_profile))
        .where(DriverLocation.id == id)
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Driver location not found")

    profile: DriverProfile | None = getattr(location, "driver_profile", None)
    if profile is None or getattr(profile, "user_id", None) != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return location
