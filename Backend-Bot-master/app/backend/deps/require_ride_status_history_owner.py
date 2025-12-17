from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.backend.deps.get_current_user import get_current_user
from app.crud import driver_profile
from app.models import Ride, RideStatusHistory, User
from app.models.driver_profile import DriverProfile


async def require_ride_status_history_owner(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> RideStatusHistory:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(
        select(RideStatusHistory)
        .options(selectinload(RideStatusHistory.ride))
        .where(RideStatusHistory.id == id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Ride status history not found")

    ride: Ride | None = getattr(item, "ride", None)
    profile: DriverProfile | None = getattr(ride, "driver_profile", None)
    if ride is None or getattr(ride, "client_id", None) != user.id and getattr(profile, "user_id", None) != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return item
