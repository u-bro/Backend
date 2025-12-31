from fastapi import Request, FastAPI
from app.logger import logger
from app.db import async_session_maker
from app.config import API_IGNORE


def install_db_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _db_session_middleware(request: Request, call_next):
        path = request.url.path
        if (
            path in API_IGNORE
            or path.startswith('/docs')
            or path.startswith('/openapi')
            or path.startswith('/redoc')
            or path.endswith('/favicon.ico')
            or path.startswith('/api/v1/health')
        ):
            return await call_next(request)

        async with async_session_maker() as session:
            request.state.session = session
            try:
                response = await call_next(request)
                await session.commit()
                return response
            except Exception:
                logger.error("Rollback session")
                await session.rollback()
                raise
