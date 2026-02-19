from typing import Dict, List
from asyncio import Task
import math, asyncio, logging, app.config
from app.services.websocket_manager import manager_driver_feed
from app.services.driver_state_storage import driver_state_storage
from app.db import async_session_maker
from app.models import Ride
from app.schemas.ride import RideSchema
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DriverFeed:
    def __init__(self):
        self._tasks: Dict[int, Task[None]] = {}
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def start_feed_task(self, user_id: int, driver_profile_id: int) -> None:
        existing = self._tasks.get(user_id)
        if existing is not None and not existing.done():
            existing.cancel()

        self._tasks[user_id] = asyncio.create_task(self._loop(user_id=user_id, driver_profile_id=driver_profile_id))

    async def stop_feed(self, user_id: int) -> None:
        task = self._tasks.pop(user_id, None)
        if task is None:
            return

        if not task.done():
            task.cancel()

    async def _loop(self, user_id: int, driver_profile_id: int) -> None:
        try:
            while manager_driver_feed.is_connected(user_id):
                async with async_session_maker() as session:
                    feed = await self.get_driver_feed(session, driver_profile_id, app.config.FEED_LIMIT)
                    await manager_driver_feed.send_personal_message(user_id, {"type": "ride_feed", "driver_profile_id": driver_profile_id, "count": len(feed), "rides": feed})

                await asyncio.sleep(app.config.FEED_PUSH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error(f"Ride feed loop error for user {user_id}: {exc}")

    async def get_driver_feed(self, session: AsyncSession, driver_profile_id: int, limit: int = 20) -> List[dict]:
        driver = driver_state_storage.get_driver(driver_profile_id)
        if not driver or not driver.is_available() or driver.latitude is None or driver.longitude is None :
            return []

        rides = await self.get_requested_rides(session, limit=limit * 2)
        relevant_rides = []
        for ride in rides:
            ride_class = ride.ride_class
            if not driver.has_permit(ride_class):
                continue

            pickup_lat = ride.pickup_lat
            pickup_lng = ride.pickup_lng
            distance = self._haversine_distance(
                driver.latitude, driver.longitude,
                float(pickup_lat), float(pickup_lng)
            )
            if distance > app.config.MAX_DISTANCE_KM:
                continue

            ride_with_distance = {**ride.model_dump(), 'distance_to_pickup_km': round(distance, 2)}
            relevant_rides.append((distance, ride_with_distance))

        relevant_rides.sort(key=lambda x: x[0])
        return [r[1] for r in relevant_rides[:limit]]

    async def get_requested_rides(self, session: AsyncSession, limit: int = 1) -> list[RideSchema]:
        stmt = select(Ride).where(and_(Ride.status == "requested", Ride.driver_profile_id.is_(None))).limit(limit)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchema.model_validate(ride) for ride in rides]

driver_feed = DriverFeed()