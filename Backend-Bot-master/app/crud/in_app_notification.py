from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app_notification import InAppNotificationSchema
from sqlalchemy import select


class InAppNotificationCrud(CrudBase[InAppNotification, InAppNotificationSchema]):
    def __init__(self) -> None:
        super().__init__(InAppNotification, InAppNotificationSchema)
    
    async def get_by_user_id(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        result = await session.execute(select(self.model).where(self.model.user_id == user_id).offset(offset).limit(page_size))
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

in_app_notification_crud = InAppNotificationCrud()
