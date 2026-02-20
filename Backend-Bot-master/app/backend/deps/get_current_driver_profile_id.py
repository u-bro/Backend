from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, and_

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
        select(DriverProfile).where(and_(DriverProfile.user_id == user.id))
    )
    driver_profile = result.scalar_one_or_none()
    if driver_profile is None:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    if not driver_profile.approved:
        raise HTTPException(status_code=403, detail="DRIVER_PROFILE_NOT_APPROVED")
    
    return int(driver_profile.id)
