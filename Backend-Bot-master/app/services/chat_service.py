import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from better_profanity import profanity

from app.models.chat_message import ChatMessage
from app.models.ride import Ride
from app.models.user import User
from app.models.role import Role
from app.models.driver_profile import DriverProfile
from app.schemas.chat_message import ChatMessageSchema, ChatMessageCreate

logger = logging.getLogger(__name__)



BANNED_WORDS = {

    "хуй", "хуя", "хуе", "хуи", "пизд", "блять", "блядь", "бля", "ебать", 
    "ебан", "ебал", "ебу", "еби", "сука", "сучк", "мудак", "мудил",
    "пидор", "пидар", "гандон", "залупа", "шлюх", "дрочи",

    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cunt",
}

LEET_REPLACEMENTS = {
    '0': 'о', '1': 'и', '3': 'е', '4': 'а', '5': 's', '6': 'б', '@': 'а',
    '$': 's', '!': 'и', '*': '', '.': '', '-': '', '_': '',
}


class MessageType:
    TEXT = "text"
    IMAGE = "image"
    LOCATION = "location"
    SYSTEM = "system"  
    VOICE = "voice"


class ModerationResult:
    def __init__(self, passed: bool, original: str, filtered: str, reason: Optional[str] = None):
        self.passed = passed
        self.original = original
        self.filtered = filtered
        self.reason = reason


class ChatService:
    def __init__(self):
        self._message_timestamps: Dict[int, List[datetime]] = defaultdict(list)
        self.rate_limit_messages = 10  
        self.rate_limit_period = 60  
        self.max_message_length = 2000
        self.min_message_length = 1
        
        # Инициализация better-profanity с дополнительными словами
        profanity.load_censor_words()
        # Добавляем наши кастомные слова к словарю библиотеки (как список)
        profanity.add_censor_words(list(BANNED_WORDS))
    
    def _normalize_text(self, text: str) -> str:
        result = text.lower()
        for leet, normal in LEET_REPLACEMENTS.items():
            result = result.replace(leet, normal)
        return result
    
    def _contains_banned_words(self, text: str) -> tuple[bool, Optional[str]]:
        # Сначала проверяем через better-profanity
        if profanity.contains_profanity(text):
            return True, "profanity"
        
        # Затем наша кастомная проверка с нормализацией
        normalized = self._normalize_text(text)
        
        for word in BANNED_WORDS:
            if word in normalized:
                return True, word
        
        return False, None
    
    def _censor_text(self, text: str) -> str:
        # Используем better-profanity для основной цензуры
        censored = profanity.censor(text)
        
        # Дополнительная цензура для наших кастомных слов
        normalized = self._normalize_text(censored)
        
        for word in BANNED_WORDS:
            if word in normalized:
                # Ищем оригинальное слово в тексте и заменяем его
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                censored = pattern.sub('*' * len(word), censored)
        
        return censored
    
    def moderate_message(self, text: str) -> ModerationResult:
        if not text:
            return ModerationResult(False, "", "", "Empty message")
        if len(text) > self.max_message_length:
            return ModerationResult(
                False, text, text[:self.max_message_length], 
                f"Message too long (max {self.max_message_length})"
            )
        
        if len(text.strip()) < self.min_message_length:
            return ModerationResult(False, text, "", "Message too short")
        has_banned, found_word = self._contains_banned_words(text)
        
        if has_banned:
            censored = self._censor_text(text)
            return ModerationResult(True, text, censored, f"Censored: {found_word}")
        
        return ModerationResult(True, text, text, None)
    
    def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.rate_limit_period)
        
        self._message_timestamps[user_id] = [
            ts for ts in self._message_timestamps[user_id] 
            if ts > cutoff
        ]
        
        if len(self._message_timestamps[user_id]) >= self.rate_limit_messages:
            return False, f"Rate limit exceeded. Max {self.rate_limit_messages} messages per {self.rate_limit_period}s"
        
        self._message_timestamps[user_id].append(now)
        return True, None
    
    async def validate_chat_access(
        self, 
        session: AsyncSession, 
        ride_id: int, 
        user_id: int
    ) -> tuple[bool, Optional[str], Optional[str]]:
        query = select(Ride).where(Ride.id == ride_id)
        result = await session.execute(query)
        ride = result.scalar_one_or_none()
        
        if not ride:
            return False, "Ride not found", None
        if ride.client_id == user_id:
            return True, None, "client"
        
        if ride.driver_profile_id:
            # Нужно проверить user_id водителя через driver_profile
            # Пока упрощённо — считаем что driver_profile_id связан с user
            # TODO: связать через driver_profile.user_id
            pass
        
        # TODO: Проверка на оператора (по роли пользователя)
        # Пока разрешаем для тестирования
        return True, None, "operator"
    
    async def save_message(
        self,
        session: AsyncSession,
        ride_id: int,
        sender_id: int,
        text: str,
        message_type: str = MessageType.TEXT,
        receiver_id: Optional[int] = None,
        attachments: Optional[Dict[str, Any]] = None,
        is_moderated: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> ChatMessageSchema:
        # Deduplication by idempotency_key
        if idempotency_key:
            query = select(ChatMessage).where(ChatMessage.idempotency_key == idempotency_key)
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                return ChatMessageSchema.model_validate(existing)

        message = ChatMessage(
            ride_id=ride_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            text=text,
            message_type=message_type,
            attachments=attachments,
            is_moderated=is_moderated,
            created_at=datetime.utcnow(),
            idempotency_key=idempotency_key,
        )
        
        session.add(message)
        await session.flush()
        await session.refresh(message)
        
        return ChatMessageSchema.model_validate(message)
    
    async def get_chat_history(
        self,
        session: AsyncSession,
        ride_id: int,
        limit: int = 50,
        before_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[ChatMessageSchema]:
        conditions = [ChatMessage.ride_id == ride_id]
        
        if before_id:
            conditions.append(ChatMessage.id < before_id)
        
        if not include_deleted:
            conditions.append(ChatMessage.deleted_at.is_(None))
        
        query = (
            select(ChatMessage)
            .where(and_(*conditions))
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        )
        
        result = await session.execute(query)
        messages = result.scalars().all()
        
        return [ChatMessageSchema.model_validate(m) for m in reversed(messages)]
    
    async def soft_delete_message(
        self,
        session: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> bool:
        query = select(ChatMessage).where(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id,
                ChatMessage.deleted_at.is_(None)
            )
        )
        
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            return False
        
        message.deleted_at = datetime.utcnow()
        await session.flush()
        return True
    
    async def edit_message(
        self,
        session: AsyncSession,
        message_id: int,
        user_id: int,
        new_text: str,
    ) -> Optional[ChatMessageSchema]:
        query = select(ChatMessage).where(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id,
                ChatMessage.deleted_at.is_(None)
            )
        )
        
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            return None
        
        moderation = self.moderate_message(new_text)
        
        message.text = moderation.filtered
        message.edited_at = datetime.utcnow()
        message.is_moderated = moderation.passed
        
        await session.flush()
        await session.refresh(message)
        
        return ChatMessageSchema.model_validate(message)
    
    async def can_access_ride_chat(self, session: AsyncSession, user_id: int, ride_id: int) -> bool:
        """Проверяет, может ли пользователь присоединиться к чату поездки.
        Доступ имеют: заказчик, водитель и админы."""
        # Получить пользователя с ролью
        user_stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        user = await session.scalar(user_stmt)
        if not user:
            return False

        # Админы имеют доступ ко всем чатам
        if user.role and user.role.code == 'admin':
            return True

        # Получить поездку с клиентом и водителем
        ride_stmt = select(Ride).options(
            selectinload(Ride.client),
            selectinload(Ride.driver_profile).selectinload(DriverProfile.user)
        ).where(Ride.id == ride_id)
        ride = await session.scalar(ride_stmt)
        if not ride:
            return False

        # Заказчик поездки
        if user_id == ride.client_id:
            return True

        # Водитель поездки
        if ride.driver_profile and ride.driver_profile.user_id == user_id:
            return True

        return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_users_with_rate_limit": len(self._message_timestamps),
            "rate_limit_config": {
                "messages": self.rate_limit_messages,
                "period_seconds": self.rate_limit_period,
            },
            "max_message_length": self.max_message_length,
            "moderation": {
                "custom_words_count": len(BANNED_WORDS),
                "leet_replacements_count": len(LEET_REPLACEMENTS),
                "uses_better_profanity": True,
            }
        }
    
    def test_profanity_detection(self, text: str) -> Dict[str, Any]:
        """Тестовый метод для проверки работы модерации"""
        has_profanity = profanity.contains_profanity(text)
        custom_check, word = self._contains_banned_words(text)
        censored = self._censor_text(text)
        
        return {
            "original": text,
            "has_profanity": has_profanity,
            "custom_check": custom_check,
            "found_word": word,
            "censored": censored,
            "is_changed": text != censored
        }

chat_service = ChatService()
