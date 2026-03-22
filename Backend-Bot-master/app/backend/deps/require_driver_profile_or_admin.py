from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.backend.deps.get_current_user import get_current_user
from app.models.user import User
from typing import TypeVar, Type

T = TypeVar("T")
def require_driver_profile_or_admin(model: Type[T]):
    async def _require_driver_profile_or_admin(request: Request, id: int, user: User = Depends(get_current_user)) -> T:
        session = getattr(request.state, "session", None)
        if session is None:
            raise HTTPException(status_code=500, detail="Database session is not available")

        result = await session.execute(select(model).options(joinedload(model.driver_profile)).where(model.id == id))
        item = result.scalar_one_or_none()
        driver_profile = getattr(item, "driver_profile", None)

        if user.role.code != "admin" and (item is None or driver_profile is None or getattr(driver_profile, "user_id", None) != user.id):
            raise HTTPException(status_code=403, detail="Forbidden")

        return item

    return _require_driver_profile_or_admin