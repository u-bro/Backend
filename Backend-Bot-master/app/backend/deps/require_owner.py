from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from app.backend.deps.get_current_user import get_current_user_id
from typing import TypeVar, Type

T = TypeVar("T")
def require_owner(model: Type[T], owner_field_name: str):
    async def _require_owner(request: Request, id: int, user_id: int = Depends(get_current_user_id)) -> T:
        session = getattr(request.state, "session", None)
        if session is None:
            raise HTTPException(status_code=500, detail="Database session is not available")

        result = await session.execute(select(model).where(model.id == id))
        item = result.scalar_one_or_none()
        if item is None or getattr(item, owner_field_name, None) != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        return item

    return _require_owner