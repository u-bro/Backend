from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import User
from .get_current_user_id import get_current_user_id

async def get_current_user(request: Request, user_id: int = Depends(get_current_user_id)) -> User:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=403, detail="User is inactive")

    return user