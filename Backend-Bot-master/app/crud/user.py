from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import update, select
from sqlalchemy.orm import joinedload
from app.crud.base import CrudBase
from app.models import User
from app.schemas.user import UserSchema, UserSchemaUpdate, UserSchemaWithRole
from fastapi import HTTPException


class UserCrud(CrudBase):
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
                raise HTTPException(status_code=409, detail="Phone number already exists")

        if "email" in update_data:
            existing_user = await self.get_by_email(session, update_data.get("email"))
            if existing_user and existing_user.id != id:
                raise HTTPException(status_code=409, detail="Email already exists")

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def get_by_id_with_role(self, session: AsyncSession, id: int) -> UserSchemaWithRole | None:
        result = await session.execute(select(self.model).options(joinedload(self.model.role)).where(self.model.id == id))
        item = result.scalar_one_or_none()
        return UserSchemaWithRole.model_validate(item) if item else None

user_crud: UserCrud = UserCrud(User, UserSchema)