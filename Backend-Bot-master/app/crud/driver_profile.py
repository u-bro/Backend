from app.crud.base import CrudBase
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileSchema, DriverProfileApprove, DriverProfileWithCars, DriverProfileCreate
from app.schemas.driver_location import DriverLocationCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from .driver_location import driver_location_crud
from app.models import Car, DriverProfileModeration
from app.config import DRIVER_PROFILE_INITIAL_RATING_AVG, DRIVER_PROFILE_INITIAL_RATING_COUNT
from datetime import datetime, timezone
from app.services.driver_profile_changes import demoderate_approved_driver, lock_driver_profile
from app.services.after_commit import add_after_commit
from app.services.driver_state_storage import driver_state_storage

CLASS_VALUE = {
    'light': 1,
    'pro': 2,
    'vip': 3,
    'elite': 4
}
ADMIN_UPDATE_SENSITIVE_FIELDS = {
    "first_name", "last_name", "middle_name", "birth_date", "photo_url",
    "license_number", "license_category", "license_issued_at",
    "license_expires_at", "experience_years", "current_class",
    "current_car_id", "classes_allowed", "status",
}


class DriverProfileCrud(CrudBase[DriverProfile, DriverProfileSchema]):
    def __init__(self) -> None:
        super().__init__(DriverProfile, DriverProfileSchema)

    async def get_paginated_with_cars(self, session: AsyncSession, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        result = await session.execute(select(self.model).options(selectinload(self.model.cars), selectinload(self.model.moderation_info)).offset(offset).limit(page_size))
        items = result.scalars().all()
        return [DriverProfileWithCars.model_validate(item) for item in items]

    async def get_by_user_id(self, session: AsyncSession, user_id: int):
        result = await session.execute(select(self.model).where(self.model.user_id == user_id))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def get_by_id_with_cars(self, session: AsyncSession, id: int):
        result = await session.execute(select(self.model).options(selectinload(self.model.cars), selectinload(self.model.moderation_info)).where(self.model.id == id))
        item = result.scalar_one_or_none()
        return DriverProfileWithCars.model_validate(item) if item else None

    async def get_by_user_id_with_cars(self, session: AsyncSession, user_id: int):
        result = await session.execute(select(self.model).options(selectinload(self.model.cars), selectinload(self.model.moderation_info)).where(self.model.user_id == user_id))
        item = result.scalar_one_or_none()
        return DriverProfileWithCars.model_validate(item) if item else None

    async def ride_count_increment(self, session: AsyncSession, id: int):
        stmt = update(self.model).where(self.model.id == id).values(ride_count=self.model.ride_count + 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def ride_count_decrement(self, session: AsyncSession, id: int):
        stmt = update(self.model).where(self.model.id == id).values(ride_count=self.model.ride_count - 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def create(self, session: AsyncSession, create_obj: DriverProfileCreate) -> DriverProfileSchema | None:
        if create_obj.classes_allowed and len(create_obj.classes_allowed):
            create_obj.classes_allowed = sorted(create_obj.classes_allowed, key=lambda x: CLASS_VALUE[x])
            create_obj.current_class = create_obj.classes_allowed[-1]

        existing = await session.execute(select(self.model).where(self.model.user_id == create_obj.user_id))
        existing_item = existing.scalar_one_or_none()
        if existing_item:
            raise HTTPException(status_code=409, detail=f"Driver profile for user {create_obj.user_id} already created")
        create_data = create_obj.model_dump()
        create_data.update(
            rating_avg=DRIVER_PROFILE_INITIAL_RATING_AVG,
            rating_count=DRIVER_PROFILE_INITIAL_RATING_COUNT,
        )
        stmt = insert(self.model).values(create_data).returning(self.model)
        result = await self.execute_get_one(session, stmt)

        driver_location = await driver_location_crud.get_by_driver_profile_id(session, result.id)
        if not driver_location:
            await driver_location_crud.create(session, DriverLocationCreate(driver_profile_id=result.id))

        return self.schema.model_validate(result) if result else None

    async def update_me(self, session: AsyncSession, id: int, update_obj):
        existing_item = await lock_driver_profile(session, id)
        existing_result = self.schema.model_validate(existing_item)
        supplied_fields = update_obj.model_fields_set
        update_data = update_obj.model_dump(include=supplied_fields, exclude_none=True)
        if not update_data:
            return existing_result

        if "classes_allowed" in update_data:
            classes = sorted(update_data["classes_allowed"], key=lambda x: CLASS_VALUE[x])
            update_data["classes_allowed"] = classes
            update_data["current_class"] = classes[-1]
        elif "current_class" in update_data:
            classes = sorted(existing_result.classes_allowed, key=lambda x: CLASS_VALUE[x])
            update_data["current_class"] = classes[-1]

        if not any(getattr(existing_item, field) != value for field, value in update_data.items()):
            return existing_result

        was_approved = existing_item.approved
        await demoderate_approved_driver(session, existing_item)

        if was_approved:
            update_data['status'] = 'waiting_approved'

        if existing_result.status == 'waiting_register':
            update_data['status'] = 'waiting_approved'

        if update_data.get('status') == 'approved':
            update_data['approved'] = True
            update_data['approved_at'] = datetime.now(timezone.utc)

        if "current_car_id" in update_data:
            car = await session.execute(select(Car).where(Car.id == update_data["current_car_id"]))
            car_result = car.scalar_one_or_none()
            if not car_result:
                raise HTTPException(status_code=404, detail="Car not found")
            if car_result.driver_profile_id != id:
                raise HTTPException(status_code=400, detail="Car does not belong to this driver profile")

        if "current_class" in update_data:
            if update_data["current_class"] not in update_data.get("classes_allowed", existing_result.classes_allowed):
                raise HTTPException(status_code=400, detail="Current class is not allowed")
        
        update_data['updated_at'] = datetime.now(timezone.utc)
        stmt = update(self.model).where(self.model.id == id).values(update_data).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if result and {"classes_allowed", "current_car_id"}.intersection(update_data):
            profile_id = result.id
            classes_allowed = result.classes_allowed
            current_car_id = result.current_car_id
            add_after_commit(
                session,
                lambda: driver_state_storage.sync_profile(
                    profile_id, classes_allowed, current_car_id
                ),
            )
        return self.schema.model_validate(result) if result else None

    async def update(self, session: AsyncSession, id: int, update_obj):
        item = await lock_driver_profile(session, id)
        update_data = update_obj.model_dump(include=update_obj.model_fields_set, exclude_none=True)
        if item.approved and ADMIN_UPDATE_SENSITIVE_FIELDS.intersection(update_data):
            raise HTTPException(
                status_code=409,
                detail="APPROVED_DRIVER_PROFILE_ADMIN_UPDATE_FORBIDDEN",
            )
        if not update_data:
            return self.schema.model_validate(item)
        if "classes_allowed" in update_data:
            classes = sorted(update_data["classes_allowed"], key=lambda value: CLASS_VALUE[value])
            update_data["classes_allowed"] = classes
            update_data["current_class"] = classes[-1]
        stmt = update(self.model).where(self.model.id == id).values(update_data).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if result and {"classes_allowed", "current_car_id"}.intersection(update_data):
            profile_id = result.id
            classes_allowed = result.classes_allowed
            current_car_id = result.current_car_id
            add_after_commit(
                session,
                lambda: driver_state_storage.sync_profile(
                    profile_id, classes_allowed, current_car_id
                ),
            )
        return self.schema.model_validate(result) if result else None

    async def approve(self, session: AsyncSession, id: int, update_obj: DriverProfileApprove):
        item = await lock_driver_profile(session, id)

        classes = sorted(update_obj.classes_allowed, key=lambda x: CLASS_VALUE[x])
        update_obj.classes_allowed = classes
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, item.id)
        if not driver_location:
            await driver_location_crud.create(session, DriverLocationCreate(driver_profile_id=id))
        stmt = (
            update(self.model)
            .where(self.model.id == item.id)
            .values(**update_obj.model_dump(exclude_none=True), current_class=classes[-1])
            .returning(self.model)
        )
        updated = await self.execute_get_one(session, stmt)
        profile_id = updated.id
        classes_allowed = updated.classes_allowed
        current_car_id = updated.current_car_id
        add_after_commit(
            session,
            lambda: driver_state_storage.sync_profile(
                profile_id, classes_allowed, current_car_id
            ),
        )
        return self.schema.model_validate(updated) if updated else None

    async def resubmit(self, session: AsyncSession, id: int):
        item = await lock_driver_profile(session, id)
        if item.status != "rejected":
            raise HTTPException(status_code=409, detail="Only rejected profiles can be resubmitted")

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(
                status="waiting_moderation",
                approved=False,
                approved_by=None,
                approved_at=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(self.model)
        )
        updated = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(updated) if updated else None

    async def moderate(self, session: AsyncSession, id: int, status: str, moderation_info_ids: list[int], admin_user_id: int, expected_updated_at: datetime, classes_allowed: list[str] | None = None):
        item = await lock_driver_profile(session, id)
        if item.updated_at != expected_updated_at:
            raise HTTPException(
                status_code=409,
                detail="DRIVER_PROFILE_CHANGED_DURING_MODERATION",
            )

        await session.execute(
            delete(DriverProfileModeration).where(DriverProfileModeration.driver_profile_id == id)
        )
        if moderation_info_ids:
            await session.execute(
                insert(DriverProfileModeration),
                [
                    {"driver_profile_id": id, "driver_moderation_info_id": reason_id}
                    for reason_id in moderation_info_ids
                ],
            )

        approved = status == "approved"
        if approved:
            classes = classes_allowed if classes_allowed is not None else item.classes_allowed
            if not classes:
                raise HTTPException(status_code=422, detail="DRIVER_CLASSES_ALLOWED_REQUIRED")
            item.classes_allowed = sorted(classes, key=lambda x: CLASS_VALUE[x])
            item.current_class = item.classes_allowed[-1]
            driver_location = await driver_location_crud.get_by_driver_profile_id(session, id)
            if not driver_location:
                await driver_location_crud.create(session, DriverLocationCreate(driver_profile_id=id))
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(
                status=status,
                approved=approved,
                approved_by=admin_user_id,
                approved_at=datetime.now(timezone.utc) if approved else None,
                classes_allowed=item.classes_allowed,
                current_class=item.current_class,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(self.model)
        )
        updated = await self.execute_get_one(session, stmt)
        if approved:
            profile_id = updated.id
            classes_allowed = updated.classes_allowed
            current_car_id = updated.current_car_id
            add_after_commit(
                session,
                lambda: driver_state_storage.sync_profile(
                    profile_id, classes_allowed, current_car_id
                ),
            )
        return self.schema.model_validate(updated) if updated else None

driver_profile_crud = DriverProfileCrud()
