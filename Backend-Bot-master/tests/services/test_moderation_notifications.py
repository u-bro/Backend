from types import SimpleNamespace

import pytest

from app.services.moderation_notifications import (
    APPROVED_EVENT,
    DOCUMENTS_AND_CAR_CONTEXT,
    DOCUMENTS_ONLY_CONTEXT,
    GENERIC_CONTEXT,
    REJECTED_EVENT,
    UPDATED_DOCUMENTS_CONTEXT,
    _approval_message,
    _classify_approval_context,
    send_moderation_notification,
)


def make_document(doc_type, status):
    return SimpleNamespace(doc_type=doc_type, status=status)


def make_profile(current_car_id=10, status="approved"):
    return SimpleNamespace(
        current_car_id=current_car_id,
        status=status,
        user_id=2,
        id=1,
        created_at=None,
        updated_at=None,
    )


@pytest.mark.parametrize(
    ("documents", "current_car_id", "expected"),
    [
        ([make_document("PASSPORT_OTHER", "approved")], None, DOCUMENTS_ONLY_CONTEXT),
        ([make_document("CAR_PHOTO_FRONT", "approved")], 10, GENERIC_CONTEXT),
        (
            [make_document("DRIVER_LICENSE_FRONT", "approved")],
            10,
            DOCUMENTS_AND_CAR_CONTEXT,
        ),
        (
            [make_document("STS_FRONT", "updated")],
            10,
            UPDATED_DOCUMENTS_CONTEXT,
        ),
        ([], None, GENERIC_CONTEXT),
    ],
)
def test_classify_approval_context(documents, current_car_id, expected):
    assert _classify_approval_context(make_profile(current_car_id), documents) == expected


def test_approval_message_selection():
    assert (
        _approval_message(DOCUMENTS_ONLY_CONTEXT)
        == "Ваши документы одобрены. Теперь вы можете принимать заказы без автомобиля."
    )
    assert (
        _approval_message(DOCUMENTS_AND_CAR_CONTEXT)
        == "Ваши документы и автомобиль одобрены. Теперь вы можете принимать заказы."
    )
    assert (
        _approval_message(UPDATED_DOCUMENTS_CONTEXT)
        == "Обновлённые документы одобрены. Теперь вы можете принимать заказы."
    )
    assert _approval_message(GENERIC_CONTEXT) == "Модерация профиля завершена успешно"


class NotificationResult:
    def __init__(self, row=None, values=None):
        self.row = row
        self.values = values or []

    def one_or_none(self):
        return self.row

    def scalars(self):
        return self

    def all(self):
        return self.values


class FakeSession:
    def __init__(self, profile, user, documents=(), reasons=()):
        self.profile = profile
        self.user = user
        self.documents = list(documents)
        self.reasons = list(reasons)
        self.executed = []

    async def execute(self, statement):
        self.executed.append(str(statement))
        if "FROM driver_documents" in str(statement):
            return NotificationResult(values=self.documents)
        if "FROM driver_moderation_info" in str(statement):
            return NotificationResult(values=self.reasons)
        return NotificationResult(row=(self.profile, self.user))


@pytest.mark.asyncio
async def test_approval_sends_matching_in_app_and_push_payload(monkeypatch):
    profile = make_profile(current_car_id=10)
    user = SimpleNamespace(id=2)
    session = FakeSession(profile, user, [make_document("PASSPORT_FRONT", "approved")])
    created = {}
    pushed = {}

    async def create_notification(notification_session, notification):
        created.update(notification.model_dump())
        return notification

    async def send_push(notification_session, user_id, payload):
        pushed.update(payload.model_dump())

    monkeypatch.setattr(
        "app.services.moderation_notifications.in_app_notification_crud.create",
        create_notification,
    )
    monkeypatch.setattr(
        "app.services.moderation_notifications.fcm_service.send_to_user",
        send_push,
    )

    await send_moderation_notification(session, profile.id, APPROVED_EVENT)

    assert created["title"] == "Заявка водителя принята"
    assert created["message"] == (
        "Ваши документы и автомобиль одобрены. Теперь вы можете принимать заказы."
    )
    assert created["data"]["notification_context"] == DOCUMENTS_AND_CAR_CONTEXT
    assert pushed["title"] == created["title"]
    assert pushed["body"] == created["message"]
    assert pushed["data"] == created["data"]


@pytest.mark.asyncio
async def test_rejection_preserves_reasons_and_matching_payload(monkeypatch):
    profile = make_profile(current_car_id=None)
    user = SimpleNamespace(id=2)
    reason = SimpleNamespace(message="Неверное фото")
    session = FakeSession(profile, user, reasons=[reason])
    created = {}
    pushed = {}

    async def create_notification(notification_session, notification):
        created.update(notification.model_dump())
        return notification

    async def send_push(notification_session, user_id, payload):
        pushed.update(payload.model_dump())

    monkeypatch.setattr(
        "app.services.moderation_notifications.in_app_notification_crud.create",
        create_notification,
    )
    monkeypatch.setattr(
        "app.services.moderation_notifications.fcm_service.send_to_user",
        send_push,
    )

    await send_moderation_notification(
        session,
        profile.id,
        REJECTED_EVENT,
        moderation_info_ids=[9],
    )

    assert created["title"] == "Заявка водителя отклонена"
    assert created["message"] == "Исправьте данные и отправьте заявку повторно: Неверное фото"
    assert created["data"]["reasons"] == ["Неверное фото"]
    assert pushed["title"] == created["title"]
    assert pushed["body"] == created["message"]
    assert pushed["data"] == created["data"]


@pytest.mark.asyncio
async def test_resubmit_keeps_existing_notification(monkeypatch):
    profile = make_profile(current_car_id=None)
    user = SimpleNamespace(id=2)
    session = FakeSession(profile, user)
    created = {}

    async def create_notification(notification_session, notification):
        created.update(notification.model_dump())
        return notification

    monkeypatch.setattr(
        "app.services.moderation_notifications.in_app_notification_crud.create",
        create_notification,
    )
    monkeypatch.setattr(
        "app.services.moderation_notifications.fcm_service.send_to_user",
        lambda *args, **kwargs: None,
    )

    await send_moderation_notification(session, profile.id, "driver_moderation_resubmitted")

    assert created["title"] == "Заявка снова на модерации"
    assert created["message"] == "Заявка водителя повторно отправлена на модерацию"
    assert "notification_context" not in created["data"]
    assert not any("FROM driver_documents" in statement for statement in session.executed)
