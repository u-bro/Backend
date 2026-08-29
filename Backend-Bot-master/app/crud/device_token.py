from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models.device_token import DeviceToken
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenSchema, DeviceTokenUpdate


@dataclass(frozen=True)
class DeviceTokenSnapshot:
    id: int
    token: str
    user_id: int
    created_at: datetime


class DeviceTokenCrud(CrudBase[DeviceToken, DeviceTokenSchema]):
    def __init__(self) -> None:
        super().__init__(DeviceToken, DeviceTokenSchema)

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> list[DeviceTokenSchema]:
        result = await session.execute(select(self.model).where(self.model.user_id == user_id))
        items = result.scalars().unique().all()
        return [self.schema.model_validate(item) for item in items]

    async def get_recipient_snapshots(
        self,
        session: AsyncSession,
        user_id: int | None = None,
    ) -> tuple[list[DeviceTokenSnapshot], int]:
        stmt = select(
            self.model.id,
            self.model.token,
            self.model.user_id,
            self.model.created_at,
        )
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)
        result = await session.execute(stmt)
        rows = result.unique().all()
        snapshots = [
            DeviceTokenSnapshot(row.id, row.token, row.user_id, row.created_at)
            for row in rows
            if row.token
        ]
        return snapshots, len({row.user_id for row in rows})

    async def get_by_user_id_and_token(self, session: AsyncSession, user_id: int, token: str) -> DeviceTokenSchema | None:
        result = await session.execute(
            select(self.model).where(self.model.user_id == user_id, self.model.token == token)
        )
        item = result.scalars().first()
        return self.schema.model_validate(item) if item else None

    async def create(self, session: AsyncSession, create_obj: DeviceTokenCreate) -> DeviceTokenSchema:
        values = create_obj.model_dump()
        stmt = (
            insert(self.model)
            .values(values)
            .on_conflict_do_update(
                index_elements=[self.model.token],
                set_={
                    "user_id": create_obj.user_id,
                    "platform": create_obj.platform,
                    "created_at": create_obj.created_at,
                },
            )
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result)

    async def delete_snapshots(
        self,
        session: AsyncSession,
        snapshots: list[DeviceTokenSnapshot],
    ) -> int:
        if not snapshots:
            return 0
        matches = [
            and_(
                self.model.id == snapshot.id,
                self.model.token == snapshot.token,
                self.model.user_id == snapshot.user_id,
                self.model.created_at == snapshot.created_at,
            )
            for snapshot in snapshots
        ]
        result = await session.execute(
            delete(self.model).where(or_(*matches))
        )
        return result.rowcount or 0

    async def delete_by_user_id_and_token(self, session: AsyncSession, user_id: int, token: str) -> DeviceTokenSchema | None:
        stmt = delete(self.model).where(self.model.user_id == user_id, self.model.token == token).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


device_token_crud = DeviceTokenCrud()
