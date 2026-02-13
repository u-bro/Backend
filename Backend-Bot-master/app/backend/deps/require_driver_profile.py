from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.backend.deps.get_current_user import get_current_user_id
from typing import TypeVar, Type

T = TypeVar("T")
def require_driver_profile(model: Type[T]):
    async def _require_driver_profile(request: Request, id: int, user_id: int = Depends(get_current_user_id)) -> T:
        session = getattr(request.state, "session", None)
        if session is None:
            raise HTTPException(status_code=500, detail="Database session is not available")

        result = await session.execute(select(model).options(joinedload(model.driver_profile)).where(model.id == id))
        item = result.scalar_one_or_none()
        driver_profile = getattr(item, "driver_profile", None)

        if item is None or driver_profile is None or getattr(driver_profile, "user_id", None) != user_id or not getattr(driver_profile, "approved", False):
            raise HTTPException(status_code=403, detail="Forbidden")

        return item

    return _require_driver_profile