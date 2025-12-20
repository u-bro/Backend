from fastapi import HTTPException, Request
from app.crud.auth import CrudAuth
from app.models import User
from app.schemas import UserSchema
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM


auth_crud = CrudAuth(User, UserSchema, JWT_SECRET_KEY, JWT_ALGORITHM)


def extract_user_id_from_token(token: str) -> int | None:
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    payload = auth_crud.verify_token(token)
    if payload is None:
        return None
    
    return payload.get("user_id")


def get_current_user_id(request: Request) -> int:
    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")
 
    user_id = extract_user_id_from_token(authorization_header)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
 
    return user_id