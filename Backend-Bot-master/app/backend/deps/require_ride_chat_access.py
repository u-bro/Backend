from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Ride
from .get_current_user import get_current_user


async def require_ride_chat_access(request: Request, ride_id: int, current_user=Depends(get_current_user)) -> Ride:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(
        select(Ride).options(selectinload(Ride.driver_profile)).where(Ride.id == ride_id)
    )
    ride = result.scalar_one_or_none()

    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    if current_user.id == ride.client_id:
        return ride

    if ride.driver_profile and getattr(ride.driver_profile, 'user_id', None) == current_user.id:
        return ride

    user_role = getattr(getattr(current_user, 'role', None), 'code', None)
    if user_role == 'admin':
        return ride

    raise HTTPException(status_code=403, detail='Access denied to ride chat')
