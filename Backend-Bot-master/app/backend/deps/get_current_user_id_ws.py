from fastapi import WebSocket, WebSocketException
from starlette.status import WS_1008_POLICY_VIOLATION

from app.crud.auth import CrudAuth
from app.models import User
from app.schemas import UserSchema
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM

auth_crud = CrudAuth(User, UserSchema, JWT_SECRET_KEY, JWT_ALGORITHM)

async def get_current_user_id_ws(websocket: WebSocket) -> int:
    token = websocket.query_params.get("token") or websocket.headers.get("authorization")
    if not token:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Missing authorization token")

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    payload = auth_crud.verify_token(token)
    if payload is None:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Invalid token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Invalid token payload")

    return user_id
