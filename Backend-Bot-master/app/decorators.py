import aiohttp
import functools

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import logger
from app.db import async_session_maker


def handle_client_error(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred: {e}")
            return None
    return wrapper


def handle_sqlalchemy_error(func):
    @functools.wraps(func)
    async def wrapper(self, session, *args, **kwargs):
        try:
            result = await func(self, session, *args, **kwargs)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Sqlalchemy Error: {str(e)[:450]}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error during Crud operation: {str(e)[:250]}")
        finally:
            await session.close()
        return False
    return wrapper