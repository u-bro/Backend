from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.crud.device_token import DeviceTokenCrud, DeviceTokenSnapshot
from app.schemas.device_token import DeviceTokenCreate
from app.schemas.push import AdminPushSendRequest, PushNotificationData


def test_admin_push_request_validates_audience_target_pair():
    with pytest.raises(ValidationError):
        AdminPushSendRequest(audience="user", title="Title", body="Body", operator_id=1, operator_name="Admin")

    with pytest.raises(ValidationError):
        AdminPushSendRequest(audience="all", user_id=2, title="Title", body="Body", operator_id=1, operator_name="Admin")


@pytest.mark.asyncio
async def test_device_token_create_is_global_atomic_upsert():
    crud = DeviceTokenCrud()
    captured = SimpleNamespace(statement=None)

    async def execute_get_one(session, statement):
        captured.statement = statement
        return SimpleNamespace(
            id=1,
            user_id=2,
            token="shared-token",
            platform="ios",
            created_at=DeviceTokenCreate(user_id=2, token="x", platform="ios").created_at,
        )

    crud.execute_get_one = execute_get_one
    result = await crud.create(
        SimpleNamespace(),
        DeviceTokenCreate(user_id=2, token="shared-token", platform="ios"),
    )

    sql = str(captured.statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (token) DO UPDATE" in sql
    assert result.user_id == 2


@pytest.mark.asyncio
async def test_invalid_cleanup_matches_exact_registration_snapshot():
    crud = DeviceTokenCrud()
    captured = SimpleNamespace(statement=None)
    created_at = datetime.now(timezone.utc)

    class Session:
        async def execute(self, statement):
            captured.statement = statement
            return SimpleNamespace(rowcount=1)

    await crud.delete_snapshots(
        Session(),
        [DeviceTokenSnapshot(7, "token", 11, created_at)],
    )

    compiled = captured.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled)
    assert "device_tokens.id = 7" in sql
    assert "device_tokens.user_id = 11" in sql
    assert "device_tokens.created_at =" in sql
    assert "device_tokens.token = 'token'" in sql


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


@pytest.mark.asyncio
async def test_batched_send_reports_permanent_invalid_tokens(monkeypatch):
    from app.services.fcm_service import FCMService

    service = FCMService()

    class UnregisteredError(Exception):
        code = "UNREGISTERED"

    async def send_to_tokens(tokens, payload):
        return SimpleNamespace(
            success_count=1,
            failure_count=1,
            responses=(
                SimpleNamespace(success=True, exception=None),
                SimpleNamespace(success=False, exception=UnregisteredError()),
            ),
        )

    monkeypatch.setattr(service, "send_to_tokens", send_to_tokens)
    result = await service.send_to_tokens_batched(
        ["valid", "invalid", "invalid"],
        PushNotificationData(title="Title"),
    )

    assert result.attempted_count == 2
    assert result.permanent_invalid_tokens == ("invalid",)


class FakeSession:
    def __init__(self, user_id=1, duplicate_id=None):
        self.user_id = user_id
        self.duplicate_id = duplicate_id
        self.history = None
        self.commits = 0
        self.scalar_calls = 0
        self.scalar_statements = []
        self.executed = []
        self.source_session = None

    async def scalar(self, statement):
        self.scalar_calls += 1
        self.scalar_statements.append(statement)
        return self.user_id if "FROM users" in str(statement) else self.duplicate_id

    async def execute(self, statement, params=None):
        self.executed.append((statement, params))

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
        return self.source_session.history if self.source_session else self.history


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def snapshots(*tokens):
    created_at = datetime.now(timezone.utc)
    return [
        DeviceTokenSnapshot(index, token, 3, created_at)
        for index, token in enumerate(tokens, start=1)
    ]


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

    async def get_recipient_snapshots(session, user_id):
        return snapshots("one", "two"), 1

    async def send_to_tokens_batched(tokens, payload):
        return SimpleNamespace(
            attempted_count=2,
            success_count=1,
            failure_count=1,
            errors=(),
        )

    monkeypatch.setattr(router_module.device_token_crud, "get_recipient_snapshots", get_recipient_snapshots)
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
    assert len(session.history.fingerprint) == 64
    assert session.commits == 3


@pytest.mark.asyncio
async def test_internal_endpoint_blocks_recent_normalized_duplicate(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")
    session = FakeSession(duplicate_id=23)
    router = router_module.PushAdminRouter(None, "/push")

    with pytest.raises(HTTPException) as exc_info:
        await router.send_from_admin(
            SimpleNamespace(state=SimpleNamespace(session=session)),
            admin_request(title="  TITLE ", body="Body\n text"),
            "secret",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "code": "ADMIN_PUSH_DUPLICATE_RECENT",
        "history_id": 23,
    }
    assert session.history is None
    assert session.executed
    duplicate_query = str(session.scalar_statements[-1])
    assert "status =" in duplicate_query
    assert "created_at >=" in duplicate_query
    assert "attempted_token_count >" in duplicate_query


@pytest.mark.asyncio
async def test_internal_endpoint_marks_empty_audience_failed(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")

    async def get_recipient_snapshots(session, user_id):
        return [], 0

    async def send_to_tokens_batched(tokens, payload):
        return SimpleNamespace(attempted_count=0, success_count=0, failure_count=0, errors=())

    monkeypatch.setattr(router_module.device_token_crud, "get_recipient_snapshots", get_recipient_snapshots)
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

    async def get_recipient_snapshots(session, user_id):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(router_module.device_token_crud, "get_recipient_snapshots", get_recipient_snapshots)
    session = FakeSession()
    rollback = SimpleNamespace(called=False)

    async def track_rollback():
        rollback.called = True

    session.rollback = track_rollback
    recovery_session = FakeSession()
    recovery_session.source_session = session
    monkeypatch.setattr(
        router_module,
        "async_session_maker",
        lambda: FakeSessionContext(recovery_session),
    )
    router = router_module.PushAdminRouter(None, "/push")

    response = await router.send_from_admin(
        SimpleNamespace(state=SimpleNamespace(session=session)),
        admin_request(),
        "secret",
    )

    assert rollback.called
    assert response.status == "failed"
    assert session.history.error_message == "Push result unknown: RuntimeError"
    assert session.commits == 1
    assert recovery_session.commits == 1


@pytest.mark.asyncio
async def test_post_send_cleanup_failure_persists_unknown_counts_in_recovery_session(monkeypatch):
    import app.backend.routers.push_notification as router_module

    monkeypatch.setattr(router_module, "PUSH_INTERNAL_TOKEN", "secret")

    async def get_recipient_snapshots(session, user_id):
        return snapshots("one", "invalid"), 1

    async def send_to_tokens_batched(tokens, payload):
        return SimpleNamespace(
            attempted_count=2,
            success_count=1,
            failure_count=1,
            errors=("FCM token failures",),
            permanent_invalid_tokens=("invalid",),
        )

    async def delete_snapshots(session, token_snapshots):
        raise RuntimeError("cleanup database error")

    session = FakeSession()
    recovery_session = FakeSession()
    recovery_session.source_session = session
    monkeypatch.setattr(router_module.device_token_crud, "get_recipient_snapshots", get_recipient_snapshots)
    monkeypatch.setattr(router_module.device_token_crud, "delete_snapshots", delete_snapshots)
    monkeypatch.setattr(router_module.fcm_service, "send_to_tokens_batched", send_to_tokens_batched)
    monkeypatch.setattr(
        router_module,
        "async_session_maker",
        lambda: FakeSessionContext(recovery_session),
    )
    router = router_module.PushAdminRouter(None, "/push")

    response = await router.send_from_admin(
        SimpleNamespace(state=SimpleNamespace(session=session)),
        admin_request(),
        "secret",
    )

    assert response.status == "unknown"
    assert response.attempted_token_count == 2
    assert response.success_count == 1
    assert response.failure_count == 1
    assert recovery_session.commits == 1
