from app.crud.base import CrudBase
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app_notification import InAppNotificationSchema


class InAppNotificationCrud(CrudBase[InAppNotification, InAppNotificationSchema]):
    def __init__(self) -> None:
        super().__init__(InAppNotification, InAppNotificationSchema)

in_app_notification_crud = InAppNotificationCrud()
