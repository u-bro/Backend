from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import update, select
from app.crud.base import CrudBase
from app.models import User
from app.schemas.user import UserSchema, UserSchemaUpdate
from fastapi import HTTPException


class CrudUser(CrudBase):
    async def delete(self, session: AsyncSession, id: int) -> UserSchema | None:
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_active=False)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def get_by_phone(self, session: AsyncSession, phone: str) -> UserSchema | None:
        stmt = select(self.model).where(self.model.phone == phone)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def get_by_email(self, session: AsyncSession, email: str) -> UserSchema | None:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def update(self, session: AsyncSession, id: int, update_obj: UserSchemaUpdate) -> UserSchema | None:
        update_data = update_obj.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(session, id)
        
        if "phone" in update_data:
            existing_user = await self.get_by_phone(session, update_data.get("phone"))
            if existing_user and existing_user.id != id:
                raise HTTPException(status_code=400, detail="Phone number already exists")

        if "email" in update_data:
            existing_user = await self.get_by_email(session, update_data.get("email"))
            if existing_user and existing_user.id != id:
                raise HTTPException(status_code=400, detail="Email already exists")

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

user_crud: CrudUser = CrudUser(User, UserSchema)