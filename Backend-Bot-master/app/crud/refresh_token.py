from app.crud.base import CrudBase
from app.models.refresh_token import RefreshToken
from app.schemas.refresh_token import RefreshTokenSchema, RefreshTokenIn, RefreshTokenCreate
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib, secrets
from app.config import REFRESH_TOKEN_SALT
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone
from app.config import REFRESH_TOKEN_EXPIRATION_DAYS


class RefreshTokenCrud(CrudBase[RefreshToken, RefreshTokenSchema]):
    def __init__(self) -> None:
        super().__init__(RefreshToken, RefreshTokenSchema)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256((token + REFRESH_TOKEN_SALT).encode()).hexdigest()
    
    @staticmethod
    def generate_token(length: int = 64) -> str:
        return secrets.token_urlsafe(length)
    
    async def create(self, session: AsyncSession, create_obj: RefreshTokenIn) -> RefreshTokenSchema:
        token = self.generate_token()
        create_obj = RefreshTokenCreate(
            user_id=create_obj.user_id,
            token=self.hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS),
            revoked_at=None,
            created_at=datetime.now(timezone.utc)
        )
        result = await super().create(session, create_obj)
        result.token = token
        return result

    async def get_by_token(self, session: AsyncSession, token: str) -> RefreshTokenSchema | None:
        result = await session.execute(select(self.model).where(self.model.token == token))
        token = result.scalar_one_or_none()
        return self.schema.model_validate(token) if token else None

    async def revoke(self, session: AsyncSession, token: str) -> None:
        await session.execute(update(self.model).where(self.model.token == token).values(revoked_at=datetime.now(timezone.utc)))

refresh_token_crud = RefreshTokenCrud()
