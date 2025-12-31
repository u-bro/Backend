from app.crud.base import CrudBase
from app.models.driver_rating import DriverRating
from app.schemas.driver_rating import DriverRatingSchema, DriverRatingAvgOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql.expression import desc
from .ride import ride_crud

class DriverRatingCrud(CrudBase[DriverRating, DriverRatingSchema]):
    def __init__(self) -> None:
        super().__init__(DriverRating, DriverRatingSchema)

    async def create(self, session: AsyncSession, create_obj, **kwargs) -> DriverRatingSchema:
        ride = await ride_crud.get_by_id(session, create_obj.ride_id)

        if ride is None or create_obj.client_id != ride.client_id:
            return "Client ID does not match the ride's client"
        
        if create_obj.driver_profile_id != ride.driver_profile_id:
            return "Driver profile ID does not match the ride's driver"
        
        existing_rating = await session.execute(
            select(self.model).where(
                self.model.ride_id == create_obj.ride_id,
                self.model.client_id == create_obj.client_id
            )
        )
        if existing_rating.scalar_one_or_none():
            return "Rating already exists for this ride"
        
        return await super().create(session, create_obj, **kwargs)

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
        return DriverRatingAvgOut(avg=result.scalar_one_or_none())

driver_rating_crud = DriverRatingCrud()
