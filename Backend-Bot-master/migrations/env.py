import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Use unified Base.metadata and import all models to register tables
from app.db import Base
import app.models  # noqa: F401 - ensures models are imported and tables registered

from app.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


config = context.config

section = config.config_ini_section
config.set_section_option(section, 'DB_HOST', DB_HOST)
config.set_section_option(section, 'DB_NAME', DB_NAME)
config.set_section_option(section, 'DB_PASS', DB_PASS)
config.set_section_option(section, 'DB_PORT', DB_PORT)
config.set_section_option(section, 'DB_USER', DB_USER)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use a single metadata for autogenerate across all declarative models
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    table_name = None
    if type_ == "table":
        table_name = name
    else:
        table = getattr(object, "table", None)
        table_name = getattr(table, "name", None)

    if table_name and (table_name.startswith("auth_") or table_name.startswith("django_")):
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
