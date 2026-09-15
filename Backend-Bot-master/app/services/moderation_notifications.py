from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.in_app_notification import in_app_notification_crud
from app.models import DriverDocument, DriverModerationInfo, DriverProfile, User
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from app.services.fcm_service import fcm_service


logger = logging.getLogger(__name__)


APPROVED_EVENT = "driver_moderation_approved"
REJECTED_EVENT = "driver_moderation_rejected"
UPDATED_DOCUMENTS_CONTEXT = "updated_documents"
DOCUMENTS_AND_CAR_CONTEXT = "documents_and_car"
DOCUMENTS_ONLY_CONTEXT = "documents_only"
GENERIC_CONTEXT = "generic"


def _is_personal_document(doc_type: str | None) -> bool:
    if doc_type is None:
        return False
    return not doc_type.startswith("CAR_PHOTO_") and doc_type.startswith(
        ("PASSPORT_", "DRIVER_LICENSE_", "STS_")
    )


def _classify_approval_context(profile: object, documents: list[object]) -> str:
    personal_documents = [
        document
        for document in documents
        if _is_personal_document(getattr(document, "doc_type", None))
    ]
    has_updated_documents = any(
        getattr(document, "status", None) == "updated"
        for document in personal_documents
    )
    has_approved_documents = any(
        getattr(document, "status", None) == "approved"
        for document in personal_documents
    )
    has_current_car = getattr(profile, "current_car_id", None) is not None

    if has_updated_documents:
        return UPDATED_DOCUMENTS_CONTEXT
    if has_approved_documents and has_current_car:
        return DOCUMENTS_AND_CAR_CONTEXT
    if has_approved_documents:
        return DOCUMENTS_ONLY_CONTEXT
    return GENERIC_CONTEXT


def _approval_message(context: str) -> str:
    if context == UPDATED_DOCUMENTS_CONTEXT:
        return "Обновлённые документы одобрены. Теперь вы можете принимать заказы."
    if context == DOCUMENTS_AND_CAR_CONTEXT:
        return "Ваши документы и автомобиль одобрены. Теперь вы можете принимать заказы."
    if context == DOCUMENTS_ONLY_CONTEXT:
        return "Ваши документы одобрены. Теперь вы можете принимать заказы без автомобиля."
    return "Модерация профиля завершена успешно"


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

    notification_context: str | None = None
    if event_type == APPROVED_EVENT:
        documents_result = await session.execute(
            select(DriverDocument).where(DriverDocument.driver_profile_id == driver_profile_id)
        )
        documents = list(documents_result.scalars().all())
        notification_context = _classify_approval_context(profile, documents)
        title = "Заявка водителя принята"
        message = _approval_message(notification_context)
    elif event_type == REJECTED_EVENT:
        title = "Заявка водителя отклонена"
        message = "Исправьте данные и отправьте заявку повторно"
        if reason_messages:
            message = f"{message}: {', '.join(reason_messages)}"
    else:
        title = "Заявка снова на модерации"
        message = "Заявка водителя повторно отправлена на модерацию"

    notification_data = {
        "type": event_type,
        "driver_profile_id": str(driver_profile_id),
        "status": str(profile.status),
        "reasons": reason_messages,
    }
    if notification_context is not None:
        notification_data["notification_context"] = notification_context
    notification = await in_app_notification_crud.create(
        session,
        InAppNotificationCreate(
            user_id=user.id,
            type=event_type,
            title=title,
            message=message[:255],
            data=notification_data,
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
                **({"notification_context": notification_context} if notification_context is not None else {}),
            }),
        )
    except Exception:
        logger.exception("Failed to send moderation notification profile_id=%s", driver_profile_id)
