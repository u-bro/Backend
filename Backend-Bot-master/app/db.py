from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import DATABASE_URL

metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Use default async engine settings (no shared connection pool) to avoid
# asyncpg "another operation is in progress" during concurrent test requests.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
