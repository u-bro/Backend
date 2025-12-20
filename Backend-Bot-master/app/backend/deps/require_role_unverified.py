from fastapi import Depends, HTTPException

from app.models import User
from app.backend.deps.get_current_user import get_current_user


def require_role_unverified(role_code: list[str] | str):
    allowed_roles = [role_code] if isinstance(role_code, str) else role_code
    
    async def _require_role(user: User = Depends(get_current_user)) -> User:
        role = getattr(user, "role", None)
        if role is None or getattr(role, "code", None) not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        return user

    return _require_role
