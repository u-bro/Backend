from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.crud.auth import CrudAuth
from app.models import User
from app.schemas import UserSchema
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM

auth_crud = CrudAuth(User, UserSchema, JWT_SECRET_KEY, JWT_ALGORITHM)
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> int:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials
    payload = auth_crud.verify_token(token)
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id