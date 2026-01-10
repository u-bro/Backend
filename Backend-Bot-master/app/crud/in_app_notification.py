from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app_notification import InAppNotificationSchema
from sqlalchemy import select, and_
from datetime import datetime, timezone
from fastapi import HTTPException


class InAppNotificationCrud(CrudBase[InAppNotification, InAppNotificationSchema]):
    def __init__(self) -> None:
        super().__init__(InAppNotification, InAppNotificationSchema)
    
    async def get_by_user_id(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        result = await session.execute(select(self.model).where(self.model.user_id == user_id).offset(offset).limit(page_size))
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

    async def get_unread_by_user_id(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        result = await session.execute(select(self.model).where(and_(self.model.user_id == user_id, self.model.read_at.is_(None))).offset(offset).limit(page_size))
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

    async def mark_all_as_read(self, session: AsyncSession, user_id: int):
        result = await session.execute(select(self.model).where(and_(self.model.user_id == user_id, self.model.read_at.is_(None))))
        notifications = result.scalars().all()
        today = datetime.now(timezone.utc)
        for notification in notifications:
            notification.read_at = today
        return [self.schema.model_validate(notification) for notification in notifications]

    async def mark_one_as_read(self, session: AsyncSession, notification_id: int, user_id: int):
        result = await session.execute(select(self.model).where(self.model.id == notification_id))
        notification = result.scalar_one_or_none()
        if notification is None:
            raise HTTPException(status_code=404, detail="Notification not found")
        if notification.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to read this notification")
        today = datetime.now(timezone.utc)
        notification.read_at = today
        return self.schema.model_validate(notification)

in_app_notification_crud = InAppNotificationCrud()
