from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.backend.deps.get_current_user import get_current_user
from app.models import Ride, User


async def require_ride_driver(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> Ride:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(select(Ride).options(selectinload(Ride.driver_profile)).where(Ride.id == id))
    ride = result.scalar_one_or_none()
    profile = getattr(ride, "driver_profile", None)
    if ride is None or profile is None:
        raise HTTPException(status_code=404, detail="Ride or driver not found")

    if getattr(profile, "user_id", None) != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return ride
