from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from app.backend.deps.get_current_user import get_current_user
from app.models import DriverProfile, User


async def require_driver_profile_owner(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> DriverProfile:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(select(DriverProfile).where(DriverProfile.id == id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    if profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return profile
