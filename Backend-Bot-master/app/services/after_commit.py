import inspect
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession


AfterCommitCallback = Callable[[], Awaitable[None] | None]
_KEY = "after_commit_callbacks"
_ROLLBACK_KEY = "after_rollback_callbacks"
logger = logging.getLogger(__name__)


def add_after_commit(session: AsyncSession, callback: AfterCommitCallback) -> None:
    session.info.setdefault(_KEY, []).append(callback)


def add_after_rollback(session: AsyncSession, callback: AfterCommitCallback) -> None:
    session.info.setdefault(_ROLLBACK_KEY, []).append(callback)


def clear_after_commit(session: AsyncSession) -> None:
    session.info.pop(_KEY, None)


def clear_after_rollback(session: AsyncSession) -> None:
    session.info.pop(_ROLLBACK_KEY, None)


async def run_after_rollback(session: AsyncSession) -> None:
    callbacks = session.info.pop(_ROLLBACK_KEY, [])
    for callback in callbacks:
        try:
            result = callback()
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("After-rollback callback failed")


async def run_after_commit(session: AsyncSession) -> None:
    callbacks = session.info.pop(_KEY, [])
    for callback in callbacks:
        try:
            result = callback()
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("After-commit callback failed")


async def commit_with_callbacks(session: AsyncSession) -> None:
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        clear_after_commit(session)
        await run_after_rollback(session)
        raise
    clear_after_rollback(session)
    await run_after_commit(session)


async def rollback_with_callbacks(session: AsyncSession) -> None:
    await session.rollback()
    clear_after_commit(session)
    await run_after_rollback(session)
