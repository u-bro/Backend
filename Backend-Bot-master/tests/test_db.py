import os

import pytest

from sqlalchemy import text

from tests.conftest import async_session_maker


@pytest.mark.asyncio
async def test_db():
    async with async_session_maker() as session:
        user_result = await session.execute(text("SELECT CURRENT_USER;"))
        db_name_result = await session.execute(text("SELECT current_database();"))

        current_user = user_result.scalar()
        current_db_name = db_name_result.scalar()

        assert current_user == 'test'
        assert current_db_name == 'test'
