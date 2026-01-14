from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
import math, logging, asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .driver_location import driver_location_crud
from .driver_profile import driver_profile_crud
from app.schemas.driver_location import DriverLocationUpdateMe, DriverLocationUpdate
from app.schemas.driver_profile import DriverProfileSchema
from app.services.websocket_manager import manager
from app.db import async_session_maker
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import MAX_DISTANCE_KM, FEED_PUSH_INTERVAL_SECONDS, FEED_LIMIT
from app.models import Ride
from app.schemas.ride import RideSchema
from sqlalchemy import and_
from sqlalchemy import select

logger = logging.getLogger(__name__)


class DriverStatus(str, Enum):
    OFFLINE = "offline"     
    ONLINE = "online"       
    BUSY = "busy"         
    NOT_CONNECTED = "not_connected"            


@dataclass
class DriverState:
    driver_profile_id: int
    user_id: int
    status: DriverStatus = DriverStatus.OFFLINE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    classes_allowed: Set[str] = field(default_factory=set)
    current_ride_id: Optional[int] = None
    rating: float = 5.0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_available(self) -> bool:
        return (
            self.status == DriverStatus.ONLINE 
            and self.current_ride_id is None
            and self.latitude is not None
        )
    
    def has_permit(self, ride_class: str) -> bool:
        return ride_class.lower() in {c.lower() for c in self.classes_allowed}


class DriverTracker:
    
    def __init__(self):
        self._drivers: Dict[int, DriverState] = {}
        self._user_to_driver: Dict[int, int] = {}
        self._class_index: Dict[str, Set[int]] = {}
        self._feed_tasks: Dict[int, asyncio.Task[None]] = {}
    
    async def register_driver(self, session: AsyncSession, driver_profile: DriverProfileSchema) -> DriverState:
        classes_set = driver_profile.classes_allowed
        driver_profile_id = driver_profile.id
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, driver_profile_id)
        if not driver_location:
            driver_location = DriverLocationUpdateMe(status=DriverStatus.OFFLINE)

        if driver_profile_id in self._drivers:
            state = self._drivers[driver_profile_id]
            state.classes_allowed = classes_set
            state.rating = driver_profile.rating_avg
            state.status=DriverStatus(driver_location.status)
            state.latitude=driver_location.latitude
            state.longitude=driver_location.longitude
        else:
            state = DriverState(
                driver_profile_id=driver_profile_id,
                user_id=driver_profile.user_id,
                classes_allowed=classes_set,
                rating=driver_profile.rating_avg,
                status=DriverStatus(driver_location.status),
                latitude=driver_location.latitude,
                longitude=driver_location.longitude
            )
            self._drivers[driver_profile_id] = state
            self._user_to_driver[driver_profile.user_id] = driver_profile_id
        
        self._update_class_index(driver_profile_id, classes_set)
        
        logger.info(f"Driver {driver_profile_id} registered with classes: {classes_set}")
        return state
    
    def update_location(self, driver_profile_id: int, latitude: float, longitude: float) -> Optional[DriverState]:
        if driver_profile_id not in self._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None
        
        state = self._drivers[driver_profile_id]
        state.latitude = latitude
        state.longitude = longitude
        state.updated_at = datetime.now(timezone.utc)
        
        return state
    
    async def update_location_by_user_id(self, session: AsyncSession, user_id: int, latitude: float, longitude: float, **kwargs) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            await driver_location_crud.update_by_driver_profile_id(session, driver_id, DriverLocationUpdateMe(latitude=latitude, longitude=longitude))
            return self.update_location(driver_id, latitude, longitude, **kwargs)
        return None
    
    async def set_status(self, driver_profile_id: int, status: DriverStatus) -> Optional[DriverState]:
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_status = state.status
        state.status = status
        state.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Driver {driver_profile_id} status: {old_status} -> {status}")

        if state.is_available():
            await self.start_feed_task(state.user_id, driver_profile_id)
        else:
            await self.stop_feed(state.user_id)

        return state
    
    async def set_status_by_user(self, session: AsyncSession, user_id: int, status: DriverStatus) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            await driver_location_crud.update_by_driver_profile_id(session, driver_id, DriverLocationUpdateMe(status=status))
            return await self.set_status(driver_id, status)
        return None
    
    async def assign_ride(self, session: AsyncSession, driver_profile_id: int, ride_id: int) -> Optional[DriverState]:
        await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status='busy'))
        
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        state.current_ride_id = ride_id
        state.status = DriverStatus.BUSY
        state.updated_at = datetime.now(timezone.utc)

        logger.info(f"Driver {driver_profile_id} assigned to ride {ride_id}")

        await self.stop_feed(state.user_id)
        return state
    
    async def release_ride(self, session: AsyncSession, driver_profile_id: int) -> Optional[DriverState]:
        driver_profile = await driver_profile_crud.get_by_id(session, driver_profile_id)
        if driver_profile:
            await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status='online'))
        
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_ride = state.current_ride_id
        state.current_ride_id = None
        state.status = DriverStatus.ONLINE
        state.updated_at = datetime.now(timezone.utc)

        logger.info(f"Driver {driver_profile_id} released from ride {old_ride}")

        await self.start_feed_task(state.user_id, driver_profile_id)
        return state
    
    def get_driver(self, driver_profile_id: int) -> Optional[DriverState]:
        return self._drivers.get(driver_profile_id)
    
    def get_driver_by_user(self, user_id: int) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            return self._drivers.get(driver_id)
        return None
    
    def get_online_count(self) -> int:
        return sum(1 for d in self._drivers.values() if d.status == DriverStatus.ONLINE)
    
    def get_busy_count(self) -> int:
        return sum(1 for d in self._drivers.values() if d.status == DriverStatus.BUSY)
    
    def get_stats(self) -> dict:
        return {
            "total_registered": len(self._drivers),
            "online": self.get_online_count(),
            "busy": self.get_busy_count(),
            "offline": sum(1 for d in self._drivers.values() if d.status == DriverStatus.OFFLINE),
        }
    
    def _update_class_index(self, driver_id: int, classes: Set[str]):
        for class_drivers in self._class_index.values():
            class_drivers.discard(driver_id)
        
        for cls in classes:
            if cls not in self._class_index:
                self._class_index[cls] = set()
            self._class_index[cls].add(driver_id)
    
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
        existing = self._feed_tasks.get(user_id)
        if existing is not None and not existing.done():
            existing.cancel()

        self._feed_tasks[user_id] = asyncio.create_task(self._feed_loop(user_id=user_id, driver_profile_id=driver_profile_id))

    async def stop_feed(self, user_id: int) -> None:
        task = self._feed_tasks.pop(user_id, None)
        if task is None:
            return

        if not task.done():
            task.cancel()
    
    async def _feed_loop(self, user_id: int, driver_profile_id: int) -> None:
        try:
            while manager.is_connected(user_id):
                async with async_session_maker() as session:
                    feed = await self.get_driver_feed(session, driver_profile_id, FEED_LIMIT)

                    await manager.send_personal_message(
                        user_id,
                        {
                            "type": "ride_feed",
                            "driver_profile_id": driver_profile_id,
                            "count": len(feed),
                            "rides": feed,
                        },
                    )

                await asyncio.sleep(FEED_PUSH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error(f"Ride feed loop error for user {user_id}: {exc}")

    async def get_driver_feed(self, session: AsyncSession, driver_profile_id: int, limit: int = 20) -> List[dict]:
        driver = driver_tracker.get_driver(driver_profile_id)
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
            
            distance = driver_tracker._haversine_distance(
                driver.latitude, driver.longitude,
                float(pickup_lat), float(pickup_lng)
            )
            if distance > MAX_DISTANCE_KM:
                continue

            ride_with_distance = {
                **ride.model_dump(),
                'distance_to_pickup_km': round(distance, 2)
            }
            relevant_rides.append((distance, ride_with_distance))
        
        relevant_rides.sort(key=lambda x: x[0])
        
        return [r[1] for r in relevant_rides[:limit]]

    async def get_requested_rides(self, session: AsyncSession, limit: int = 1) -> list[RideSchema]:
        stmt = select(Ride).where(and_(Ride.status == "requested", Ride.driver_profile_id.is_(None))).limit(limit)
        result = await session.execute(stmt)
        rides = result.scalars().all()
        return [RideSchema.model_validate(ride) for ride in rides]

driver_tracker = DriverTracker()
