from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.in_app_notification import in_app_notification_crud
from app.models import DriverModerationInfo, DriverProfile, User
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from app.services.fcm_service import fcm_service


logger = logging.getLogger(__name__)


async def send_moderation_notification(
    session: AsyncSession,
    driver_profile_id: int,
    event_type: str,
    moderation_info_ids: list[int] | None = None,
) -> None:
    profile_result = await session.execute(
        select(DriverProfile, User)
        .join(User, User.id == DriverProfile.user_id)
        .where(DriverProfile.id == driver_profile_id)
    )
    row = profile_result.one_or_none()
    if not row:
        return

    profile, user = row
    reason_messages: list[str] = []
    if moderation_info_ids:
        reasons_result = await session.execute(
            select(DriverModerationInfo).where(DriverModerationInfo.id.in_(moderation_info_ids))
        )
        reason_messages = [reason.message for reason in reasons_result.scalars().all()]

    if event_type == "driver_moderation_approved":
        title = "Заявка водителя принята"
        message = "Модерация профиля завершена успешно"
    elif event_type == "driver_moderation_rejected":
        title = "Заявка водителя отклонена"
        message = "Исправьте данные и отправьте заявку повторно"
        if reason_messages:
            message = f"{message}: {', '.join(reason_messages)}"
    else:
        title = "Заявка снова на модерации"
        message = "Заявка водителя повторно отправлена на модерацию"

    data = {
        "type": event_type,
        "driver_profile_id": str(driver_profile_id),
        "status": str(profile.status),
        "reasons": reason_messages,
    }
    notification = await in_app_notification_crud.create(
        session,
        InAppNotificationCreate(
            user_id=user.id,
            type=event_type,
            title=title,
            message=message[:255],
            data=data,
            dedup_key=f"{event_type}:{driver_profile_id}:{profile.updated_at or profile.created_at}",
        ),
    )
    if notification is None:
        return

    try:
        await fcm_service.send_to_user(
            session,
            user.id,
            PushNotificationData(title=title, body=message[:255], data={
                "type": event_type,
                "driver_profile_id": str(driver_profile_id),
                "status": str(profile.status),
                "reasons": reason_messages,
            }),
        )
    except Exception:
        logger.exception("Failed to send moderation notification profile_id=%s", driver_profile_id)
