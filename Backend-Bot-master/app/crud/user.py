from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import update
from app.crud.base import CrudBase
from app.models import User
from app.schemas import UserSchema


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


user_crud: CrudUser = CrudUser(User, UserSchema)