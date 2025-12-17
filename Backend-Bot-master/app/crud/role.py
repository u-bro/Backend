from app.crud.base import CrudBase
from app.models import Role
from app.schemas.role import RoleSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select


class RoleCrud(CrudBase[Role, RoleSchema]):
    def __init__(self) -> None:
        super().__init__(Role, RoleSchema)

    async def get_by_code(self, session: AsyncSession, code: str):
        result = await session.execute(select(self.model).where(self.model.code == code))
        role = result.scalar_one_or_none()
        return self.schema.model_validate(role) if role else None

role_crud = RoleCrud()
