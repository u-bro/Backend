import asyncio
from datetime import datetime, timezone
from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import insert, update, delete, text
from sqlalchemy.orm import joinedload
from app.crud.base import CrudBase
from .commission import commission_crud
from .ride_status_history import ride_status_history_crud
from .driver_profile import driver_profile_crud
from .driver_location import driver_location_crud
from .in_app_notification import in_app_notification_crud
from .driver_location_sender import driver_location_sender
from .driver_tracker import driver_tracker, DriverStatus
from app.models import Ride, Commission, RideDriversRequest, ChatMessage
from app.schemas.ride import RideSchema, RideSchemaHistory, RideSchemaWithRating, RideSchemaWithDriverProfile, RideSchemaUpdateByClient
from app.schemas.ride_status_history import RideStatusHistoryCreate
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.push import PushNotificationData
from fastapi import HTTPException
from app.config import RIDE_SECONDS_LIMIT
from app.db import async_session_maker
from app.services.fcm_service import fcm_service


STATUSES = {
    "requested",
    "waiting_commission",
    "accepted",
    "on_the_way",
    "arrived",
    "started",
    "completed",
    "canceled",
}

ALLOWED_TRANSITIONS = {
    "requested": {"canceled"},
    'waiting_commission': {"accepted", "canceled"},
    "accepted": {"on_the_way", "canceled"},
    'on_the_way': {"arrived", "canceled"},
    'arrived': {"started", "canceled"},
    "started": {"completed", "canceled"},
}


class RideCrud(CrudBase[Ride, RideSchema]):

    @staticmethod
    def _calculate_commission_amount(expected_fare: float | None, commission: Commission) -> float | None:
        return max(commission.fixed_amount, 0.1) + (expected_fare * commission.percentage / 100) if expected_fare else 0.1

    @staticmethod
    def _add_commission(data: dict, commission: Commission):
        expected_fare = data.get('expected_fare', 0)
        commission_amount = RideCrud._calculate_commission_amount(expected_fare, commission)
        data["commission_amount"] = commission_amount

    async def create(self, session: AsyncSession, create_obj) -> RideSchema | None:
        data = create_obj.model_dump()
        await self.cancel_rides_by_user_id(session, data.get('client_id'))
        commission = await commission_crud.get_by_id(session,  data.get("commission_id"))

        self._add_commission(data, commission)
        stmt = insert(self.model).values(data).returning(self.model)
        ride = await self.execute_get_one(session, stmt)
        if not ride:
            raise HTTPException(status_code=400, detail="Ride wasn't created")
        await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=ride.id, from_status=None, to_status='requested', changed_by=create_obj.client_id, created_at=datetime.now(timezone.utc)))
        return self.schema.model_validate(ride)

    async def update(self, session: AsyncSession, id: int, update_obj, user_id: int) -> RideSchema | None:
        existing_result = await session.execute(select(self.model).where(self.model.id == id))
        existing = existing_result.scalar_one_or_none()

        data = update_obj.model_dump(exclude_none=True)

        if data.get('expected_fare'):
            commission_id = data.get("commission_id", existing.commission_id)
            commission = await commission_crud.get_by_id(session,  int(commission_id))
            self._add_commission(data, commission)

        if not data:
            return await self.get_by_id(session, id)
        
        if update_obj.status == 'started' or update_obj.status == 'canceled':
            await driver_location_sender.stop_task(existing.client_id)

        if update_obj.status and existing.status != update_obj.status:
            if not self._is_status_transition_allowed(existing.status, update_obj.status):
                raise HTTPException(status_code=400, detail="Incorrect ride status transition")
            await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=existing.id, from_status=existing.status, to_status=update_obj.status, changed_by=int(user_id), created_at=datetime.now(timezone.utc)))

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        return self.schema.model_validate(result)

    @staticmethod
    def _is_status_transition_allowed(from_status: str, to_status: str) -> bool:
        if to_status not in STATUSES or to_status not in ALLOWED_TRANSITIONS.get(from_status, []):
            return False

        return True

    async def accept(self, session: AsyncSession, id: int, update_obj, user_id: int) -> RideSchema | None:
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, update_obj.driver_profile_id)
        if not driver_location:
            raise HTTPException(status_code=404, detail="Driver location not found")
        if driver_location.status == 'busy':
            raise HTTPException(status_code=409, detail="Driver already have accepted ride")
        
        ride = await self.get_by_id(session, id)
        if not ride:
            raise HTTPException(status_code=404, detail='Ride not found')
        
        commission = await commission_crud.get_by_id(session, ride.commission_id)
        if not commission:
            raise HTTPException(status_code=404, detail='Commission not found')

        expected_fare = update_obj.offer_fare
        stmt = (
            update(self.model)
            .where(and_(self.model.id == id, self.model.driver_profile_id.is_(None)))
            .values(driver_profile_id=update_obj.driver_profile_id, status=update_obj.status, expected_fare=expected_fare, commission_amount=self._calculate_commission_amount(expected_fare, commission))
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        await ride_status_history_crud.create(session, RideStatusHistoryCreate(ride_id=result.id, from_status='requested', to_status=update_obj.status, changed_by=user_id, created_at=datetime.now(timezone.utc)))
        await driver_profile_crud.ride_count_increment(session, update_obj.driver_profile_id)
        return self.schema.model_validate(result)

    async def delete(self, session: AsyncSession, id: int):
        stmt = delete(self.model).where(self.model.id == id).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        await driver_profile_crud.ride_count_decrement(session, result.driver_profile_id)
        return self.schema.model_validate(result)
    
    async def cancel_rides_by_user_id(self, session: AsyncSession, user_id: int):
        stmt = select(self.model).where(and_(self.model.status.in_(["requested", "waiting_commission", "accepted", "on_the_way", "arrived", "started"]), self.model.client_id == user_id))
        result = await session.execute(stmt)
        existing_rides = result.scalars().all()
        if not existing_rides or not len(existing_rides):
            return
        ids = [ride.id for ride in existing_rides]
        driver_profile_ids = [ride.driver_profile_id for ride in existing_rides]
        client_ids = [ride.client_id for ride in existing_rides]

        update_stmt_rides = update(self.model).where(self.model.id.in_(ids)).values(status="canceled")
        await session.execute(update_stmt_rides)

        for id in driver_profile_ids:
            await driver_tracker.release_ride(session, id)
        
        for id in client_ids:
            await driver_location_sender.stop_task(id)
        
        requests = await session.execute(update(RideDriversRequest).where(RideDriversRequest.ride_id.in_(ids)).values(status="rejected").returning(RideDriversRequest))
        for request in requests.scalars().all():
            await driver_tracker.set_status_by_driver(session, request.driver_profile_id, DriverStatus.ONLINE)
        
        ride = self.schema.model_validate(existing_rides[0])
        await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=user_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена, т.к. была создана новая", data=ride.model_dump(mode='json'), dedup_key=f"{ride.id}_canceled"))

    async def get_by_client_id(self, session: AsyncSession, client_id: int, order_by: str | None = None) -> list[RideSchema]:
        stmt = select(self.model).where(self.model.client_id == client_id).order_by(text(order_by) if order_by else None)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [self.schema.model_validate(ride) for ride in rides]

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> list[RideSchema]:
        stmt = select(self.model).where(self.model.driver_profile_id == driver_profile_id)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [self.schema.model_validate(ride) for ride in rides]

    async def get_by_client_id_paginated(self, session: AsyncSession, client_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchemaHistory]:
        offset = (page - 1) * page_size
        stmt = select(self.model).where(self.model.client_id == client_id).order_by(text(order_by) if order_by else None).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchemaHistory.model_validate(ride) for ride in rides]

    async def get_paginated_as_client_or_driver_with_chats(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchema]:
        offset = (page - 1) * page_size
        driver_profile = await driver_profile_crud.get_by_user_id(session, user_id)
        driver_profile_id = getattr(driver_profile, 'id', None)

        last_chat_at_sq = (
            select(
                ChatMessage.ride_id.label("ride_id"),
                func.max(ChatMessage.created_at).label("last_chat_at"),
            )
            .where(ChatMessage.deleted_at.is_(None))
            .group_by(ChatMessage.ride_id)
            .subquery()
        )

        stmt = (
            select(self.model)
            .join(last_chat_at_sq, last_chat_at_sq.c.ride_id == self.model.id)
            .where(
                and_(
                    self.model.driver_profile_id.is_not(None),
                    or_(
                        self.model.client_id == user_id,
                        self.model.driver_profile_id == driver_profile_id
                    ),
                )
            )
            .order_by(last_chat_at_sq.c.last_chat_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchema.model_validate(ride) for ride in rides]

    async def get_paginated_as_client_with_chats(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchema]:
        offset = (page - 1) * page_size

        last_chat_at_sq = (
            select(
                ChatMessage.ride_id.label("ride_id"),
                func.max(ChatMessage.created_at).label("last_chat_at"),
            )
            .where(ChatMessage.deleted_at.is_(None))
            .group_by(ChatMessage.ride_id)
            .subquery()
        )

        stmt = (
            select(self.model)
            .join(last_chat_at_sq, last_chat_at_sq.c.ride_id == self.model.id)
            .where(
                and_(
                    self.model.driver_profile_id.is_not(None),
                    self.model.client_id == user_id
                )
            )
            .order_by(last_chat_at_sq.c.last_chat_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchema.model_validate(ride) for ride in rides]
    
    async def get_paginated_as_driver_with_chats(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchema]:
        offset = (page - 1) * page_size
        driver_profile = await driver_profile_crud.get_by_user_id(session, user_id)
        driver_profile_id = getattr(driver_profile, 'id', None)

        last_chat_at_sq = (
            select(
                ChatMessage.ride_id.label("ride_id"),
                func.max(ChatMessage.created_at).label("last_chat_at"),
            )
            .where(ChatMessage.deleted_at.is_(None))
            .group_by(ChatMessage.ride_id)
            .subquery()
        )

        stmt = (
            select(self.model)
            .join(last_chat_at_sq, last_chat_at_sq.c.ride_id == self.model.id)
            .where(
                and_(
                    self.model.driver_profile_id.is_not(None),
                    self.model.driver_profile_id == driver_profile_id
                )
            )
            .order_by(last_chat_at_sq.c.last_chat_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchema.model_validate(ride) for ride in rides]

    async def get_by_driver_profile_id_paginated(self, session: AsyncSession, driver_profile_id: int, page: int = 1, page_size: int = 10, order_by: str | None = None) -> list[RideSchemaHistory]:
        offset = (page - 1) * page_size
        stmt = select(self.model).where(self.model.driver_profile_id == driver_profile_id).order_by(text(order_by) if order_by else None).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchemaHistory.model_validate(ride) for ride in rides]

    async def get_active_ride_by_client_id(self, session: AsyncSession, client_id: int) -> RideSchema | None:
        stmt = select(self.model).where(and_(self.model.client_id == client_id, self.model.status.in_(["requested", "waiting_commission", "accepted", "on_the_way", "arrived", "started"])))
        result = await session.execute(stmt)
        ride = result.scalar_one_or_none()
        return self.schema.model_validate(ride) if ride else None

    async def get_active_ride_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> RideSchema | None:
        result = await session.execute(select(self.model).where(and_(self.model.status.in_(["waiting_commission", "accepted", "on_the_way", "arrived", "started"]), Ride.driver_profile_id == driver_profile_id)))
        ride = result.scalar_one_or_none()
        return self.schema.model_validate(ride) if ride else None

    async def get_by_id_with_rating(self, session: AsyncSession, id: int) -> RideSchemaWithRating | None:
        result = await session.execute(select(self.model).options(joinedload(self.model.driver_rating)).where(self.model.id == id))
        item = result.scalar_one_or_none()
        return RideSchemaWithRating.model_validate(item) if item else None

    async def get_by_id_with_driver_profile(self, session: AsyncSession, id: int) -> RideSchemaWithDriverProfile | None:
        result = await session.execute(select(self.model).options(joinedload(self.model.driver_profile)).where(self.model.id == id))
        item = result.scalar_one_or_none()
        return RideSchemaWithDriverProfile.model_validate(item) if item else None

    async def get_last_by_client_id(self, session: AsyncSession, client_id: int):
        result = await session.execute(select(self.model).where(self.model.client_id == client_id).order_by(text('created_at desc')).limit(1))
        ride = result.scalar_one_or_none()
        return self.schema.model_validate(ride) if ride else None

    async def cancel_ride_if_timeout(self, id: int, client_id: int) -> None:
        await asyncio.sleep(RIDE_SECONDS_LIMIT)
        async with async_session_maker() as session:
            ride = await self.get_by_id(session, id)
            if ride and ride.status == 'requested':
                updated_ride = await self.update(session, id, RideSchemaUpdateByClient(status='canceled'), client_id)
                requests = await session.execute(update(RideDriversRequest).where(RideDriversRequest.ride_id == updated_ride.id).values(status="rejected").returning(RideDriversRequest))
                for request in requests.scalars().all():
                    await driver_tracker.set_status_by_driver(session, request.driver_profile_id, DriverStatus.ONLINE)
                await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=client_id, type="ride_canceled", title="Поездка отменена", message="Поездка отменена из-за таймаута", data=updated_ride.model_dump(mode='json'), dedup_key=f"{updated_ride.id}_canceled"))
                await fcm_service.send_to_user(session, client_id, PushNotificationData(title='Поездка отменена', body='Поездка отменена из-за таймаута'))
            await session.commit()

ride_crud = RideCrud(Ride, RideSchema)
