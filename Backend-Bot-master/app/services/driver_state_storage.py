from app.enum import DriverStatus
from typing import Dict, Optional
from app.dataclass import DriverState
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.driver_location import driver_location_crud
from app.schemas.driver_location import DriverLocationUpdateMe
from app.schemas.driver_profile import DriverProfileSchema

logger = logging.getLogger(__name__)


class DriverStateStorage:
    def __init__(self):
        self._drivers: Dict[int, DriverState] = {}
        self._user_to_driver: Dict[int, int] = {}

    async def register_driver(self, session: AsyncSession, driver_profile: DriverProfileSchema) -> DriverState:
        classes_set = driver_profile.classes_allowed
        driver_profile_id = driver_profile.id
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, driver_profile_id)
        if not driver_location:
            driver_location = DriverLocationUpdateMe(status=DriverStatus.OFFLINE)

        if driver_profile_id in self._drivers:
            state = self._drivers[driver_profile_id]
            state.classes_allowed = classes_set
            state.status=DriverStatus(driver_location.status)
            state.latitude=driver_location.latitude
            state.longitude=driver_location.longitude
        else:
            state = DriverState(
                driver_profile_id=driver_profile_id,
                user_id=driver_profile.user_id,
                classes_allowed=classes_set,
                status=DriverStatus(driver_location.status),
                latitude=driver_location.latitude,
                longitude=driver_location.longitude
            )
            self._drivers[driver_profile_id] = state
            self._user_to_driver[driver_profile.user_id] = driver_profile_id

        logger.info(f"Driver {driver_profile_id} registered with classes: {classes_set}")
        return state

    def get_driver(self, driver_profile_id: int) -> Optional[DriverState]:
        return self._drivers.get(driver_profile_id)

    def get_driver_by_user(self, user_id: int) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        return self._drivers.get(driver_id)

    def get_stats(self) -> dict:
        return {
            "total_registered": len(self._drivers),
            "online": sum(1 for d in self._drivers.values() if d.status == DriverStatus.ONLINE),
            "busy": sum(1 for d in self._drivers.values() if d.status == DriverStatus.BUSY),
            "offline": sum(1 for d in self._drivers.values() if d.status == DriverStatus.OFFLINE),
        }

driver_state_storage = DriverStateStorage()