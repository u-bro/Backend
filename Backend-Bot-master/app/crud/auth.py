import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from app.crud.base import CrudBase
from app.schemas import UserSchema, AuthSchemaRegister, DriverProfileCreate, RefreshTokenVerifyRequest, TokenResponse, UserSchemaCreate
from app.schemas.refresh_token import RefreshTokenIn
from app.logger import logger
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINTUES
from app.models import User
from .role import role_crud
from .driver_profile import driver_profile_crud
from .refresh_token import refresh_token_crud
from fastapi import HTTPException


class CrudAuth(CrudBase):
    def __init__(self, model, schema, secret_key: str, algorithm: str = "HS256"):
        super().__init__(model, schema)
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: int, expires_delta: timedelta = timedelta(minutes=JWT_EXPIRATION_MINTUES)) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def get_by_phone(self, session: AsyncSession, phone: str) -> UserSchema | None:
        result = await session.execute(select(self.model).where(self.model.phone == phone))
        user = result.scalar_one_or_none()
        return self.schema.model_validate(user) if user else None

    async def register_user(self, session: AsyncSession, register_obj: AuthSchemaRegister) -> UserSchema | None:
        existing_user = await self.get_by_phone(session, register_obj.phone)
        if existing_user:
            logger.warning(f"User with phone {register_obj.phone} already exists")
            raise HTTPException(status_code=409, detail="User with phone already exists")

        role = await role_crud.get_by_code(session, register_obj.role_code)
        if not role:
            logger.warning(f"Role with code \'{register_obj.role_code}\' not found")
            raise HTTPException(status_code=404, detail="Role not found")
        
        new_user = await super().create(session, UserSchemaCreate(phone=register_obj.phone, is_active=True, role_id=role.id))

        if register_obj.role_code == 'driver':
            await driver_profile_crud.create(session, DriverProfileCreate(user_id=new_user.id, approved=False))
        
        return self.schema.model_validate(new_user)

    async def login_or_register(self, session: AsyncSession, phone: str) -> (UserSchema, bool):
        user = await self.get_by_phone(session, phone)
        is_registred = False
        if not user:
            user = await self.register_user(session, AuthSchemaRegister(phone=phone, role_code='driver'))
            is_registred = True
            
        return user, is_registred

    async def refresh(self, session: AsyncSession, refresh_obj: RefreshTokenVerifyRequest) -> TokenResponse | None:
        token_hash = refresh_token_crud.hash_token(refresh_obj.refresh_token)
        
        found_token = await refresh_token_crud.get_by_token(session, token_hash)
        if not found_token or found_token.revoked_at:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        await refresh_token_crud.revoke(session, token_hash)

        access_token = self.create_access_token(found_token.user_id, timedelta(minutes=JWT_EXPIRATION_MINTUES))
        refresh_token = await refresh_token_crud.create(session, RefreshTokenIn(user_id=found_token.user_id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token.token
        )

auth_crud = CrudAuth(User, UserSchema, JWT_SECRET_KEY, JWT_ALGORITHM)
