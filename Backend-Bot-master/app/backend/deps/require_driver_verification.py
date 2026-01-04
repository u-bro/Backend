from fastapi import Depends, HTTPException, Request

from app.models import User
from app.backend.deps.get_current_user import get_current_user



async def require_driver_verification(request: Request, user: User = Depends(get_current_user)) -> User:
    role = getattr(user, "role", None)
    if role is None or role.code != "driver":
        raise HTTPException(status_code=403, detail="Forbidden")

    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    driver = getattr(user, "driver_profile", None)
    if driver is None or not getattr(driver, "approved", False):
        raise HTTPException(status_code=403, detail="Driver is not verified")

    return user
