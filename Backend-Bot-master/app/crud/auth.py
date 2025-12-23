import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from app.crud.base import CrudBase
from app.schemas import UserSchema, AuthSchemaRegister
from app.logger import logger
from .role import role_crud

class CrudAuth(CrudBase):
    def __init__(self, model, schema, secret_key: str, algorithm: str = "HS256"):
        super().__init__(model, schema)
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: int, expires_delta: timedelta = timedelta(hours=24)) -> str:
        expire = datetime.utcnow() + expires_delta
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return None

    async def get_by_phone(self, session: AsyncSession, phone: str) -> UserSchema | None:
        result = await session.execute(select(self.model).where(self.model.phone == phone))
        user = result.scalar_one_or_none()
        return self.schema.model_validate(user) if user else None

    async def register_user(self, session: AsyncSession, register_obj: AuthSchemaRegister) -> UserSchema | None:
        existing_user = await self.get_by_phone(session, register_obj.phone)
        if existing_user:
            logger.warning(f"User with phone {register_obj.phone} already exists")
            return None

        role = await role_crud.get_by_code(session, "user")
        if not role:
            logger.warning(f"Role with code \'user\' not found")
            return None
        
        user_data = {
            "username": register_obj.username,
            "phone": register_obj.phone,
            "is_active": True,
            "role_id": role.id
        }
        
        new_user = self.model(**user_data)
        session.add(new_user)
        await session.flush()
        await session.commit()
        
        return self.schema.model_validate(new_user)

    async def login_user(self, session: AsyncSession, phone: str) -> UserSchema | None:
        user = await self.get_by_phone(session, phone)
        if not user:
            logger.warning(f"Invalid phone number")
            return None

        return user
