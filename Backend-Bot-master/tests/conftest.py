import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class _DummyAsyncSession:
    async def commit(self) -> None:
        return None

    async def execute(self, query) -> None:
        return None

    async def rollback(self) -> None:
        return None


class _DummySessionContext:
    def __init__(self) -> None:
        self._session = _DummyAsyncSession()

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _DummyFCMService:
    async def send_to_token(self, payload):
        return "message-id"

    async def send_to_topic(self, payload):
        return "message-id"

    async def send_to_user(self, session, user_id, payload):
        return SimpleNamespace(success_count=1, failure_count=0)


class _DummyWebhookDispatcher:
    async def dispatch_webhook(self, session, payload):
        return None


@pytest.fixture
def app_instance(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASS", "test")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", "terminal")
    monkeypatch.setenv("TBANK_TERMINAL_PASSWORD", "password")

    fake_fcm_module = types.ModuleType("app.services.fcm_service")
    fake_fcm_module.fcm_service = _DummyFCMService()
    monkeypatch.setitem(sys.modules, "app.services.fcm_service", fake_fcm_module)

    fake_webhook_module = types.ModuleType("app.services.webhook_dispatcher")
    fake_webhook_module.webhook_dispatcher = _DummyWebhookDispatcher()
    monkeypatch.setitem(sys.modules, "app.services.webhook_dispatcher", fake_webhook_module)

    sys.modules.pop("app.backend.main", None)
    main_module = importlib.import_module("app.backend.main")

    db_middleware_module = importlib.import_module("app.backend.middlewares.db")
    monkeypatch.setattr(
        db_middleware_module,
        "async_session_maker",
        lambda *args, **kwargs: _DummySessionContext(),
    )

    return main_module.app


@pytest.fixture
def client(app_instance):
    with TestClient(app_instance) as test_client:
        yield test_client
    app_instance.dependency_overrides.clear()
