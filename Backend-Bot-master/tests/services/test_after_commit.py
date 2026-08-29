import pytest

from app.services.after_commit import (
    add_after_commit,
    add_after_rollback,
    clear_after_commit,
    clear_after_rollback,
    run_after_commit,
    run_after_rollback,
)


class Session:
    def __init__(self):
        self.info = {}


@pytest.mark.asyncio
async def test_after_commit_runs_callbacks_once_in_order():
    session = Session()
    calls = []
    add_after_commit(session, lambda: calls.append("sync"))

    async def async_callback():
        calls.append("async")

    add_after_commit(session, async_callback)
    await run_after_commit(session)
    await run_after_commit(session)
    assert calls == ["sync", "async"]


@pytest.mark.asyncio
async def test_after_commit_is_cleared_on_rollback_boundary():
    session = Session()
    calls = []
    add_after_commit(session, lambda: calls.append("called"))
    clear_after_commit(session)
    await run_after_commit(session)
    assert calls == []


@pytest.mark.asyncio
async def test_after_rollback_runs_callbacks_once_and_can_be_cleared():
    session = Session()
    calls = []
    add_after_rollback(session, lambda: calls.append("cleanup"))
    await run_after_rollback(session)
    await run_after_rollback(session)
    assert calls == ["cleanup"]

    add_after_rollback(session, lambda: calls.append("unexpected"))
    clear_after_rollback(session)
    await run_after_rollback(session)
    assert calls == ["cleanup"]
