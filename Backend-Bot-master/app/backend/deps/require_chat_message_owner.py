from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from app.backend.deps.get_current_user import get_current_user
from app.models import ChatMessage, User


async def require_chat_message_owner(
    request: Request,
    id: int,
    user: User = Depends(get_current_user),
) -> ChatMessage:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=500, detail="Database session is not available")

    result = await session.execute(select(ChatMessage).where(ChatMessage.id == id))
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="Chat message not found")

    if message.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return message
