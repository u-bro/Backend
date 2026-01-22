from datetime import datetime, timezone
from app.enum import DriverStatus
from typing import Optional
from app.dataclass import DriverState
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .driver_location import driver_location_crud
from .driver_feed import driver_feed
from .driver_profile import driver_profile_crud
from app.services.driver_state_storage import driver_state_storage
from app.schemas.driver_location import DriverLocationUpdateMe, DriverLocationUpdate

logger = logging.getLogger(__name__)


class DriverTracker:

    def update_location(self, driver_profile_id: int, latitude: float, longitude: float) -> Optional[DriverState]:
        if driver_profile_id not in driver_state_storage._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None

        state = driver_state_storage._drivers[driver_profile_id]
        state.latitude = latitude
        state.longitude = longitude
        state.updated_at = datetime.now(timezone.utc)

        return state

    async def update_location_by_user_id(self, session: AsyncSession, user_id: int, latitude: float, longitude: float, **kwargs) -> Optional[DriverState]:
        driver_id = driver_state_storage._user_to_driver.get(user_id, 0)
        await driver_location_crud.update_by_driver_profile_id(session, driver_id, DriverLocationUpdateMe(latitude=latitude, longitude=longitude))
        return self.update_location(driver_id, latitude, longitude, **kwargs)

    async def _set_status(self, driver_profile_id: int, status: DriverStatus) -> Optional[DriverState]:
        if driver_profile_id not in driver_state_storage._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None

        state = driver_state_storage._drivers[driver_profile_id]
        old_status = state.status
        state.status = status
        state.updated_at = datetime.now(timezone.utc)
        logger.info(f"Driver {driver_profile_id} status: {old_status} -> {status}")

        if state.is_available():
            await driver_feed.start_feed_task(state.user_id, driver_profile_id)
        else:
            await driver_feed.stop_feed(state.user_id)

        return state

    async def set_status_by_user(self, session: AsyncSession, user_id: int, status: DriverStatus) -> Optional[DriverState]:
        driver_id = driver_state_storage._user_to_driver.get(user_id, 0)
        await driver_location_crud.update_by_driver_profile_id(session, driver_id, DriverLocationUpdate(status=status))
        return await self._set_status(driver_id, status)

    async def set_status_by_driver(self, session: AsyncSession, driver_profile_id: int, status: DriverStatus) -> Optional[DriverState]:
        await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status=status))
        return await self._set_status(driver_profile_id, status)

    async def assign_ride(self, session: AsyncSession, driver_profile_id: int, ride_id: int) -> Optional[DriverState]:
        await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status='busy'))

        if driver_profile_id not in driver_state_storage._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None

        state = driver_state_storage._drivers[driver_profile_id]
        state.current_ride_id = ride_id
        state.status = DriverStatus.BUSY
        state.updated_at = datetime.now(timezone.utc)
        logger.info(f"Driver {driver_profile_id} assigned to ride {ride_id}")

        await driver_feed.stop_feed(state.user_id)
        return state

    async def release_ride(self, session: AsyncSession, driver_profile_id: int) -> Optional[DriverState]:
        driver_profile = await driver_profile_crud.get_by_id(session, driver_profile_id)
        if driver_profile:
            await driver_location_crud.update_by_driver_profile_id(session, driver_profile_id, DriverLocationUpdate(status='online'))

        if driver_profile_id not in driver_state_storage._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None

        state = driver_state_storage._drivers[driver_profile_id]
        old_ride = state.current_ride_id
        state.current_ride_id = None
        state.status = DriverStatus.ONLINE
        state.updated_at = datetime.now(timezone.utc)
        logger.info(f"Driver {driver_profile_id} released from ride {old_ride}")

        await driver_feed.start_feed_task(state.user_id, driver_profile_id)
        return state

driver_tracker = DriverTracker()
