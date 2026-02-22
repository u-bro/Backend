from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from better_profanity import profanity
from app.models.chat_message import ChatMessage
from app.schemas.chat_message import ChatMessageSchema, ChatMessageHistory
from app.logger import logger
from .websocket_manager import manager
from app.crud.ride import ride_crud
from app.crud.user import user_crud
from app.enum import MessageType, RoleCode


class ChatService:
    def __init__(self):
        self._message_timestamps: Dict[int, List[datetime]] = defaultdict(list)
        self.rate_limit_messages = 60
        self.rate_limit_period = 60
        self.max_message_length = 2000
        self.min_message_length = 1

        profanity.load_censor_words()

    def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.rate_limit_period)

        self._message_timestamps[user_id] = [
            ts for ts in self._message_timestamps[user_id]
            if ts > cutoff
        ]

        if len(self._message_timestamps[user_id]) >= self.rate_limit_messages:
            return False, f"Rate limit exceeded. Max {self.rate_limit_messages} messages per {self.rate_limit_period}s"

        self._message_timestamps[user_id].append(now)
        return True, None

    async def verify_ride_user(self, session: AsyncSession, ride_id: int, user_id: int) -> bool:
        ride = await ride_crud.get_by_id_with_driver_profile(session, ride_id)

        if not ride:
            logger.error(f"Ride {ride_id} not found")
            return False

        driver_profile = ride.driver_profile
        if not driver_profile:
            logger.error(f"Driver profile not found for ride {ride_id}")
            return False

        if ride.client_id != user_id and driver_profile.user_id != user_id:
            logger.error(f"User {user_id} is not a client or driver for ride {ride_id}")
            return False

        return True

    async def save_message(self, session: AsyncSession, message: ChatMessage) -> ChatMessageSchema:
        session.add(message)
        await session.flush()
        await session.refresh(message)
        result = ChatMessageSchema.model_validate(message)
        await session.commit()
        return result

    async def save_message_and_send_to_ride(self, session: AsyncSession, ride_id: int, text: str, sender_id: int | None = None, message_type: str = MessageType.TEXT, receiver_id: Optional[int] = None, attachments: Optional[Dict[str, Any]] = None, is_moderated: bool = True) -> ChatMessageSchema:
        message = {
            "ride_id": ride_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "text": text,
            "message_type": message_type,
            "attachments": attachments,
            "is_moderated": is_moderated,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.save_message(session, ChatMessage(**message))
        await manager.send_to_ride(session, ride_id, message)
        return result

    async def get_my_chats(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10) -> List[ChatMessageHistory]:
        user = await user_crud.get_by_id_with_role(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        rides = await ride_crud.get_paginated_as_driver_with_chats(session, user_id, page, page_size, "updated_at desc") if user.role.code == RoleCode.DRIVER else await ride_crud.get_paginated_as_client_with_chats(session, user_id, page, page_size, "updated_at desc")
        ride_ids = [ride.id for ride in rides if ride.driver_profile_id]
        query = select(ChatMessage).where(and_(ChatMessage.ride_id.in_(ride_ids), ChatMessage.deleted_at.is_(None)))
        result = await session.execute(query)
        messages = result.scalars().all()
        my_chats = []
        for ride_id in ride_ids:
            ride_messages = [m for m in messages if m.ride_id == ride_id]
            ride_messages.sort(key=lambda x: x.edited_at or x.created_at, reverse=True)
            chat = ChatMessageHistory(ride_id=ride_id, last_message=ChatMessageSchema.model_validate(ride_messages[0]).model_dump(mode='json'))
            my_chats.append(chat)

        return my_chats

    async def get_chat_history(self, session: AsyncSession, ride_id: int, page_size: int = 50, page: int = 1, include_deleted: bool = False, current_user_id: int | None = None) -> List[ChatMessageSchema]:
        conditions = [ChatMessage.ride_id == ride_id]

        if not include_deleted:
            conditions.append(ChatMessage.deleted_at.is_(None))
        print((page - 1) * page_size)
        print(page_size)
        query = (
            select(ChatMessage)
            .where(and_(*conditions))
            .order_by(ChatMessage.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await session.execute(query)
        messages = result.scalars().all()

        result = [ChatMessageSchema.model_validate(m) for m in messages]
        if current_user_id:
            result = [ChatMessageSchema(**message.model_dump(mode='json', exclude={'message_type'}), message_type='me' if current_user_id == message.sender_id else message.message_type) for message in result]
        return result

    async def mark_message_read(self, session: AsyncSession, ride_id: int, message_id: int, user_id: int) -> Optional[ChatMessageSchema]:
        is_ride_participant = await self.verify_ride_user(session=session, ride_id=ride_id, user_id=user_id)
        if not is_ride_participant:
            return None

        query = select(ChatMessage).where(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.ride_id == ride_id,
                ChatMessage.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        if not message:
            return None

        message.is_read = True
        return ChatMessageSchema.model_validate(message)

    async def mark_ride_messages_read(self, session: AsyncSession, ride_id: int, user_id: int, up_to_id: Optional[int] = None) -> int:
        is_ride_participant = await self.verify_ride_user(session=session, ride_id=ride_id, user_id=user_id)
        if not is_ride_participant:
            return 0

        conditions = [
            ChatMessage.ride_id == ride_id,
            ChatMessage.deleted_at.is_(None),
            ChatMessage.sender_id.is_not(None),
            ChatMessage.sender_id != user_id,
            ChatMessage.is_read.is_(False),
        ]
        if up_to_id is not None:
            conditions.append(ChatMessage.id <= up_to_id)

        stmt = (
            update(ChatMessage)
            .where(and_(*conditions))
            .values(is_read=True)
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(stmt)
        return int(result.rowcount or 0)

    async def soft_delete_message(self, session: AsyncSession, message_id: int) -> bool:
        query = select(ChatMessage).where(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.deleted_at.is_(None)
            )
        )

        result = await session.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return False

        message.deleted_at = datetime.now(timezone.utc)
        return True

    async def edit_message(self, session: AsyncSession, message_id: int, new_text: str) -> Optional[ChatMessageSchema]:
        query = select(ChatMessage).where(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.deleted_at.is_(None)
            )
        )

        result = await session.execute(query)
        message = result.scalar_one_or_none()
        if not message:
            return None

        message.text = new_text
        message.edited_at = datetime.now(timezone.utc)

        return ChatMessageSchema.model_validate(message)

    async def delete_messages_by_ride_ids(self, session: AsyncSession, ride_ids: List[int]):
        now = datetime.now(timezone.utc)
        deleted = await session.execute(update(ChatMessage).where(and_(ChatMessage.ride_id.in_(ride_ids), ChatMessage.deleted_at.is_(None))).values(deleted_at=now).returning(ChatMessage.id))
        return deleted.scalars().all()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_users_with_rate_limit": len(self._message_timestamps),
            "rate_limit_config": {
                "messages": self.rate_limit_messages,
                "period_seconds": self.rate_limit_period,
            },
            "max_message_length": self.max_message_length,
            "moderation": {
                "uses_better_profanity": True,
            }
        }



chat_service = ChatService()
