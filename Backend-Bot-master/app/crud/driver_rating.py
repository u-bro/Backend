from app.crud.base import CrudBase
from app.models.driver_rating import DriverRating
from app.schemas.driver_rating import DriverRatingSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql.expression import desc


class DriverRatingCrud(CrudBase[DriverRating, DriverRatingSchema]):
    def __init__(self) -> None:
        super().__init__(DriverRating, DriverRatingSchema)

    async def avg_rating(self, session: AsyncSession, driver_id: int, count: int = 5):
        subq = (
            select(self.model.rate)
            .where(self.model.driver_profile_id == driver_id)
            .order_by(desc(self.model.created_at))
            .limit(count)
            .subquery()
        )

        result = await session.execute(
            select(func.avg(subq.c.rate))
        )
        return result.scalar_one_or_none()

driver_rating_crud = DriverRatingCrud()
