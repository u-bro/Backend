from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.push import AdminPushSendRequest, PushNotificationData


def test_admin_push_request_validates_audience_target_pair():
    with pytest.raises(ValidationError):
        AdminPushSendRequest(audience="user", title="Title", body="Body", operator_id=1, operator_name="Admin")

    with pytest.raises(ValidationError):
        AdminPushSendRequest(audience="all", user_id=2, title="Title", body="Body", operator_id=1, operator_name="Admin")


@pytest.mark.asyncio
async def test_batched_send_deduplicates_and_splits(monkeypatch):
    from app.services.fcm_service import FCMService

    service = FCMService()
    batches = []

    async def send_to_tokens(tokens, payload):
        batches.append(list(tokens))
        return SimpleNamespace(success_count=len(tokens), failure_count=0)

    monkeypatch.setattr(service, "send_to_tokens", send_to_tokens)
    tokens = [f"token-{index}" for index in range(501)] + ["token-0"]

    result = await service.send_to_tokens_batched(tokens, PushNotificationData(title="Title", body="Body"))

    assert [len(batch) for batch in batches] == [500, 1]
    assert result.attempted_count == 501
    assert result.success_count == 501
    assert result.failure_count == 0


@pytest.mark.asyncio
async def test_batched_send_continues_after_batch_failure(monkeypatch):
    from app.services.fcm_service import FCMService

    service = FCMService()
    calls = 0

    async def send_to_tokens(tokens, payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("secret token must not leak")
        return SimpleNamespace(success_count=len(tokens), failure_count=0)

    monkeypatch.setattr(service, "send_to_tokens", send_to_tokens)
    result = await service.send_to_tokens_batched(
        [f"token-{index}" for index in range(501)],
        PushNotificationData(title="Title", body="Body"),
    )

    assert calls == 2
    assert result.success_count == 1
    assert result.failure_count == 500
    assert result.errors == ("FCM batch failed: RuntimeError",)


class FakeSession:
    def __init__(self, user_id=1):
        self.user_id = user_id
        self.history = None
        self.commits = 0

    async def scalar(self, statement):
        return self.user_id

    def add(self, history):
        history.id = 17
        self.history = history

    async def flush(self):
        return None

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        return None

    async def get(self, model, history_id):
        return self.history


def admin_request(**overrides):
    data = {
        "audience": "user",
        "user_id": 3,
        "title": "Title",
        "body": "Body",
        "operator_id": 1,
        "operator_name": "Admin",
    }
    data.update(overrides)
    return AdminPushSendRequest(**data)


@pytest.mark.asyncio
async def test_internal_endpoint_rejects_invalid_token(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")
    router = router_module.PushAdminRouter(None, "/push")
    request = SimpleNamespace(state=SimpleNamespace(session=FakeSession()))

    with pytest.raises(HTTPException) as exc_info:
        await router.send_from_admin(request, admin_request(), "wrong")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_internal_endpoint_rejects_unknown_user(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")
    router = router_module.PushAdminRouter(None, "/push")
    request = SimpleNamespace(state=SimpleNamespace(session=FakeSession(user_id=None)))

    with pytest.raises(HTTPException) as exc_info:
        await router.send_from_admin(request, admin_request(), "secret")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_internal_endpoint_saves_aggregated_result(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")

    async def get_recipients(session, user_id):
        return ["one", "two"], 1

    async def send_to_tokens_batched(tokens, payload):
        return SimpleNamespace(
            attempted_count=2,
            success_count=1,
            failure_count=1,
            errors=(),
        )

    monkeypatch.setattr(router_module.device_token_crud, "get_recipients", get_recipients)
    monkeypatch.setattr(router_module.fcm_service, "send_to_tokens_batched", send_to_tokens_batched)
    session = FakeSession()
    request = SimpleNamespace(state=SimpleNamespace(session=session))
    router = router_module.PushAdminRouter(None, "/push")

    response = await router.send_from_admin(request, admin_request(), "secret")

    assert response.history_id == 17
    assert response.status == "partial"
    assert response.success_count == 1
    assert response.failure_count == 1
    assert session.history.operator_name == "Admin"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_internal_endpoint_marks_empty_audience_failed(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")

    async def get_recipients(session, user_id):
        return [], 0

    async def send_to_tokens_batched(tokens, payload):
        return SimpleNamespace(attempted_count=0, success_count=0, failure_count=0, errors=())

    monkeypatch.setattr(router_module.device_token_crud, "get_recipients", get_recipients)
    monkeypatch.setattr(router_module.fcm_service, "send_to_tokens_batched", send_to_tokens_batched)
    session = FakeSession()
    router = router_module.PushAdminRouter(None, "/push")

    response = await router.send_from_admin(
        SimpleNamespace(state=SimpleNamespace(session=session)),
        admin_request(audience="all", user_id=None),
        "secret",
    )

    assert response.status == "failed"
    assert session.history.error_message == "No device tokens"


@pytest.mark.asyncio
async def test_internal_endpoint_recovers_transaction_to_finalize_failure(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")

    async def get_recipients(session, user_id):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(router_module.device_token_crud, "get_recipients", get_recipients)
    session = FakeSession()
    rollback = SimpleNamespace(called=False)

    async def track_rollback():
        rollback.called = True

    session.rollback = track_rollback
    router = router_module.PushAdminRouter(None, "/push")

    response = await router.send_from_admin(
        SimpleNamespace(state=SimpleNamespace(session=session)),
        admin_request(),
        "secret",
    )

    assert rollback.called
    assert response.status == "failed"
    assert session.history.error_message == "Push result unknown: RuntimeError"
    assert session.commits == 2
