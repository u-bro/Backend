from fastapi import Depends, HTTPException, Request
from sqlalchemy import desc, select

from app.models import User
from app.models.phone_verification import PhoneVerification
from app.backend.deps.get_current_user import get_current_user


def require_role(role_code: str | list[str]):
    allowed_roles = [role_code] if isinstance(role_code, str) else role_code

    async def _require_role(request: Request, user: User = Depends(get_current_user)) -> User:
        role = getattr(user, "role", None)
        if role is None or getattr(role, "code", None) not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        session = getattr(request.state, "session", None)
        if session is None:
            raise HTTPException(status_code=500, detail="Database session is not available")

        result = await session.execute(
            select(PhoneVerification)
            .where(PhoneVerification.user_id == user.id)
            .order_by(desc(PhoneVerification.created_at))
            .limit(1)
        )
        last_verification = result.scalar_one_or_none()
        if last_verification is None or getattr(last_verification, "status", None) != "confirmed":
            raise HTTPException(status_code=403, detail="Phone is not verified")

        if role.code == "driver":
            driver = getattr(user, "driver_profile", None)
            if driver is None or not getattr(driver, "approved", False):
                raise HTTPException(status_code=403, detail="Driver is not verified")

        return user

    return _require_role