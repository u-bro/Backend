from app.crud.base import CrudBase
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from fastapi import HTTPException


class DriverProfileCrud(CrudBase[DriverProfile, DriverProfileSchema]):
    def __init__(self) -> None:
        super().__init__(DriverProfile, DriverProfileSchema)

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
        update_data = update_obj.model_dump(exclude_none=True)
        if not update_data:
            return existing_result

        if "current_class" in update_data:
            if update_data["current_class"] not in update_data.get("classes_allowed", existing_result.classes_allowed):
                raise HTTPException(status_code=400, detail="Current class is not allowed")
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

driver_profile_crud = DriverProfileCrud()
