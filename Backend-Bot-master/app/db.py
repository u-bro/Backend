from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import DATABASE_URL

metadata = MetaData()
Base = declarative_base(metadata=metadata)

engine = create_async_engine(
    DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=200,  # Increase the pool size to 20 connections
    max_overflow=100,  # Allow up to 10 additional connections
    pool_timeout=300,  # Set the pool timeout to 30 seconds
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
