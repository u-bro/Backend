from fastapi.testclient import TestClient
import asyncio
import pytest
from app.backend.main import app

####
from tests.fixtures import start_postgres_container
from app.db import async_session_maker
####


GLOBAL_CLIENT = None
GLOBAL_TELEGRAM_DATA = None


def pytest_sessionstart(session):
    global GLOBAL_CLIENT
    global GLOBAL_TELEGRAM_DATA
    GLOBAL_CLIENT = TestClient(app)

    GLOBAL_TELEGRAM_DATA = ''


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()