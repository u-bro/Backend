from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from app.backend.deps.get_current_user import get_current_user
from app.models import Ride, User


async def require_ride_client(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> Ride:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(select(Ride).where(Ride.id == id))
    ride = result.scalar_one_or_none()
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride.client_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return ride
