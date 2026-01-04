from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from app.backend.deps.get_current_user import get_current_user
from app.models import DriverProfile, User


async def get_current_driver_profile_id(
    request: Request,
    user: User = Depends(get_current_user),
) -> int:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(
        select(DriverProfile.id).where(DriverProfile.user_id == user.id)
    )
    driver_profile_id = result.scalar_one_or_none()
    if driver_profile_id is None:
        raise HTTPException(status_code=403, detail="Driver profile not found")

    return int(driver_profile_id)
