from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import math, logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import driver_location_crud
from app.schemas.driver_location import DriverLocationUpdateMe, DriverLocationUpdate

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
    OFFLINE_TIMEOUT_SECONDS = 120 
    
    def __init__(self):
        self._drivers: Dict[int, DriverState] = {}
        self._user_to_driver: Dict[int, int] = {}
        self._class_index: Dict[str, Set[int]] = {}
    
    async def register_driver(self, session: AsyncSession, driver_profile_id: int, user_id: int, classes_allowed: List[str], rating: float = 5.0) -> DriverState:
        classes_set = {c.lower() for c in classes_allowed}
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, driver_profile_id)
        if not driver_location:
            driver_location = DriverLocationUpdateMe(status=DriverStatus.OFFLINE)

        if driver_profile_id in self._drivers:
            state = self._drivers[driver_profile_id]
            state.classes_allowed = classes_set
            state.rating = rating
            state.status=DriverStatus(driver_location.status)
            state.latitude=driver_location.latitude
            state.longitude=driver_location.longitude
        else:
            state = DriverState(
                driver_profile_id=driver_profile_id,
                user_id=user_id,
                classes_allowed=classes_set,
                rating=rating,
                status=DriverStatus(driver_location.status),
                latitude=driver_location.latitude,
                longitude=driver_location.longitude
            )
            self._drivers[driver_profile_id] = state
            self._user_to_driver[user_id] = driver_profile_id
        
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
    
    def set_status(self, driver_profile_id: int, status: DriverStatus) -> Optional[DriverState]:
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_status = state.status
        state.status = status
        state.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Driver {driver_profile_id} status: {old_status} -> {status}")
        return state
    
    async def set_status_by_user(self, session: AsyncSession, user_id: int, status: DriverStatus) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            await driver_location_crud.update_by_driver_profile_id(session, driver_id, DriverLocationUpdateMe(status=status))
            return self.set_status(driver_id, status)
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
        return state
    
    async def release_ride(self, session: AsyncSession, driver_profile_id: int) -> Optional[DriverState]:
        await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status='online'))
        
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_ride = state.current_ride_id
        state.current_ride_id = None
        state.status = DriverStatus.ONLINE
        state.updated_at = datetime.now(timezone.utc)

        logger.info(f"Driver {driver_profile_id} released from ride {old_ride}")
        return state
    
    def get_driver(self, driver_profile_id: int) -> Optional[DriverState]:
        return self._drivers.get(driver_profile_id)
    
    def get_driver_by_user(self, user_id: int) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            return self._drivers.get(driver_id)
        return None
    
    def get_available_drivers(self, ride_class: Optional[str] = None, center_lat: Optional[float] = None, center_lng: Optional[float] = None, radius_km: float = 10.0, limit: int = 50) -> List[DriverState]:
        candidates = []
        
        if ride_class:
            driver_ids = self._class_index.get(ride_class.lower(), set())
            drivers = [self._drivers[did] for did in driver_ids if did in self._drivers]
        else:
            drivers = list(self._drivers.values())
        
        for driver in drivers:
            if not driver.is_available():
                continue
            
            if ride_class and not driver.has_permit(ride_class):
                continue
            
            distance = None
            if center_lat is not None and center_lng is not None:
                if driver.latitude is None or driver.longitude is None:
                    continue
                
                distance = self._haversine_distance(
                    center_lat, center_lng,
                    driver.latitude, driver.longitude
                )
                
                if distance > radius_km:
                    continue
            
            candidates.append((driver, distance))
        
        candidates.sort(key=lambda x: (x[1] if x[1] else 0, -x[0].rating))
        
        return [c[0] for c in candidates[:limit]]
    
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
    
    def cleanup_stale(self) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.OFFLINE_TIMEOUT_SECONDS)
        count = 0
        
        for driver in self._drivers.values():
            if driver.status != DriverStatus.OFFLINE and driver.updated_at < threshold:
                driver.status = DriverStatus.OFFLINE
                count += 1
                logger.info(f"Driver {driver.driver_profile_id} auto-offline (stale)")
        
        return count
    
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

driver_tracker = DriverTracker()
