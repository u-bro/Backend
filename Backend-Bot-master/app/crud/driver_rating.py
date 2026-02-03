from app.crud.base import CrudBase
from app.models.driver_rating import DriverRating
from app.schemas.driver_rating import DriverRatingSchema, DriverRatingAvgOut, DriverRatingCreate, DriverRatingUpdate
from app.schemas.driver_profile import DriverProfileUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.sql.expression import desc
from .ride import ride_crud
from .driver_profile import driver_profile_crud
from fastapi import HTTPException


class DriverRatingCrud(CrudBase[DriverRating, DriverRatingSchema]):
    def __init__(self) -> None:
        super().__init__(DriverRating, DriverRatingSchema)

    async def create(self, session: AsyncSession, create_obj: DriverRatingCreate, **kwargs) -> DriverRatingSchema:
        ride = await ride_crud.get_by_id(session, create_obj.ride_id)

        if ride is None or create_obj.client_id != ride.client_id:
            raise HTTPException(status_code=400, detail="Client ID does not match the ride's client")
        
        if create_obj.driver_profile_id != ride.driver_profile_id:
            raise HTTPException(status_code=400, detail="Driver profile ID does not match the ride's driver")
        
        existing_rating = await session.execute(
            select(self.model).where(
                self.model.ride_id == create_obj.ride_id,
                self.model.client_id == create_obj.client_id
            )
        )
        if existing_rating.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Rating already exists for this ride")
        
        driver_profile = await driver_profile_crud.get_by_id(session, create_obj.driver_profile_id)
        if driver_profile is None:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        result = await super().create(session, create_obj, **kwargs)

        rating_avg = await self.avg_rating(session, create_obj.driver_profile_id)
        await driver_profile_crud.update(session, driver_profile.id, DriverProfileUpdate(rating_count=driver_profile.rating_count + 1, rating_avg=rating_avg.avg))
        
        return result

    async def update(self, session: AsyncSession, id: int, update_obj: DriverRatingUpdate) -> DriverRatingSchema | None:
        update_data = update_obj.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(session, id)
        
        existing_rating = await self.get_by_id(session, id)
        if existing_rating is None:
            return None
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None

        driver_profile = await driver_profile_crud.get_by_id(session, result.driver_profile_id)
        if driver_profile is None:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        rating_avg = await self.avg_rating(session, result.driver_profile_id)
        await driver_profile_crud.update(session, driver_profile.id, DriverProfileUpdate(rating_avg=rating_avg.avg))
        return self.schema.model_validate(result)

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
