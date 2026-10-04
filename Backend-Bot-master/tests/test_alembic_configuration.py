import inspect
import unittest
from pathlib import Path

import asyncpg
from alembic.config import Config
from sqlalchemy.ext.asyncio import async_engine_from_config


class AlembicConnectionConfigurationTests(unittest.TestCase):
    def test_migration_connection_arguments_are_supported_by_asyncpg(self):
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        for key, value in {
            "DB_USER": "test",
            "DB_PASS": "test",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "test",
        }.items():
            config.set_main_option(key, value)

        engine = async_engine_from_config(config.get_section(config.config_ini_section))
        self.assertNotIn("async_fallback", engine.url.query)
        args, kwargs = engine.dialect.create_connect_args(engine.url)
        inspect.signature(asyncpg.connect).bind(*args, **kwargs)
