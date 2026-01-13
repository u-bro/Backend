from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CrudBase
from app.models.device_token import DeviceToken
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenSchema


class DeviceTokenCrud(CrudBase[DeviceToken, DeviceTokenSchema]):
    def __init__(self) -> None:
        super().__init__(DeviceToken, DeviceTokenSchema)

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> list[DeviceTokenSchema]:
        result = await session.execute(select(self.model).where(self.model.user_id == user_id))
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

    async def get_by_user_id_and_token(self, session: AsyncSession, user_id: int, token: str) -> DeviceTokenSchema | None:
        result = await session.execute(
            select(self.model).where(self.model.user_id == user_id, self.model.token == token)
        )
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def create(self, session: AsyncSession, create_obj: DeviceTokenCreate) -> DeviceTokenSchema:
        existing = await self.get_by_user_id_and_token(session, create_obj.user_id, create_obj.token)
        if existing is not None:
            return existing

        stmt = insert(self.model).values(create_obj.model_dump()).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result)

    async def delete_by_user_id_and_token(self, session: AsyncSession, user_id: int, token: str) -> DeviceTokenSchema | None:
        stmt = delete(self.model).where(self.model.user_id == user_id, self.model.token == token).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


device_token_crud = DeviceTokenCrud()
