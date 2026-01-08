from app.crud.base import CrudBase
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileSchema, DriverProfileApprove
from app.schemas.driver_location import DriverLocationCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from fastapi import HTTPException
from .driver_location import driver_location_crud


class DriverProfileCrud(CrudBase[DriverProfile, DriverProfileSchema]):
    def __init__(self) -> None:
        super().__init__(DriverProfile, DriverProfileSchema)

    async def get_by_user_id(self, session: AsyncSession, user_id: int):
        result = await session.execute(select(self.model).where(self.model.user_id == user_id))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def ride_count_increment(self, session: AsyncSession, id: int):
        stmt = update(self.model).where(self.model.id == id).values(ride_count=self.model.ride_count + 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def ride_count_decrement(self, session: AsyncSession, id: int):
        stmt = update(self.model).where(self.model.id == id).values(ride_count=self.model.ride_count - 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def update(self, session: AsyncSession, id: int, update_obj):
        existing_result = await self.get_by_id(session, id)
        if not existing_result:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        update_data = update_obj.model_dump(exclude_none=True)
        if not update_data:
            return existing_result

        if "current_class" in update_data:
            if update_data["current_class"] not in update_data.get("classes_allowed", existing_result.classes_allowed):
                raise HTTPException(status_code=400, detail="Current class is not allowed")
        
        return await super().update(session, id, update_data)

    async def approve(self, session: AsyncSession, id: int, update_obj: DriverProfileApprove):
        existing = await session.execute(select(self.model).where(self.model.id == id))
        item = existing.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        driver_location = await driver_location_crud.get_by_driver_profile_id(session, item.id)
        if not driver_location:
            await driver_location_crud.create(session, DriverLocationCreate(driver_profile_id=id))
        return await super().update(session, item.id, update_obj)

driver_profile_crud = DriverProfileCrud()
