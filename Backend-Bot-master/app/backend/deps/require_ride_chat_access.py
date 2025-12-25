from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.backend.deps.get_current_user import get_current_user
from app.models import Ride, User, DriverProfile


async def require_ride_chat_access(
    request: Request,
    ride_id: int,
    user: User = Depends(get_current_user),
) -> Ride:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")
    result = await session.execute(
        select(Ride).options(
            selectinload(Ride.driver_profile).selectinload(DriverProfile.user)
        ).where(Ride.id == ride_id)
    )
    ride = result.scalar_one_or_none()
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    if getattr(user, "role", None) and getattr(user.role, "code", None) == "admin":
        return ride
    if getattr(ride, "client_id", None) == getattr(user, "id", None):
        return ride
    profile = getattr(ride, "driver_profile", None)
    if profile and getattr(profile, "user_id", None) == getattr(user, "id", None):
        return ride
    raise HTTPException(status_code=403, detail="Forbidden: no access to ride chat")
