from app.enum import DriverStatus
from typing import Dict, Optional
from app.dataclass import DriverState
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.driver_location import driver_location_crud
from app.schemas.driver_location import DriverLocationUpdateMe
from app.schemas.driver_profile import DriverProfileSchema
from app.schemas.driver_location import DriverLocationUpdate
from app.const import ACTIVE_RIDE_STATUSES
from app.models import Ride, RideDriversRequest
from sqlalchemy import select
from app.services.after_commit import add_after_commit

logger = logging.getLogger(__name__)


class DriverStateStorage:
    def __init__(self):
        self._drivers: Dict[int, DriverState] = {}
        self._user_to_driver: Dict[int, int] = {}

    async def register_driver(self, session: AsyncSession, driver_profile: DriverProfileSchema) -> DriverState:
        classes_set = driver_profile.classes_allowed
        driver_profile_id = driver_profile.id
        car_id = driver_profile.current_car_id
        driver_location = await driver_location_crud.get_by_driver_profile_id(session, driver_profile_id)
        if not driver_location:
            driver_location = DriverLocationUpdateMe(status=DriverStatus.OFFLINE)

        active_ride_id = await session.scalar(
            select(Ride.id).where(
                Ride.driver_profile_id == driver_profile_id,
                Ride.status.in_(ACTIVE_RIDE_STATUSES),
            ).limit(1)
        )
        has_pending = await session.scalar(
            select(RideDriversRequest.id).where(
                RideDriversRequest.driver_profile_id == driver_profile_id,
                RideDriversRequest.status == "requested",
            ).limit(1)
        )
        if active_ride_id is not None:
            reconciled_status = DriverStatus.BUSY
        elif driver_location.status == DriverStatus.OFFLINE:
            reconciled_status = DriverStatus.OFFLINE
        elif has_pending is not None:
            reconciled_status = DriverStatus.WAITING_RIDE
        else:
            reconciled_status = DriverStatus.ONLINE

        if driver_location.status != reconciled_status and getattr(driver_location, "id", None):
            driver_location = await driver_location_crud.update(
                session,
                driver_location.id,
                DriverLocationUpdate(status=reconciled_status),
            )

        state = DriverState(
            driver_profile_id=driver_profile_id,
            user_id=driver_profile.user_id,
            classes_allowed=classes_set,
            status=reconciled_status,
            latitude=driver_location.latitude,
            longitude=driver_location.longitude,
            car_id=car_id,
        )
        state.current_ride_id = active_ride_id
        add_after_commit(session, lambda: self._publish_driver(state))

        logger.info(f"Driver {driver_profile_id} registered with classes: {classes_set}")
        return state

    def _publish_driver(self, state: DriverState) -> None:
        self._drivers[state.driver_profile_id] = state
        self._user_to_driver[state.user_id] = state.driver_profile_id

    def get_driver(self, driver_profile_id: int) -> Optional[DriverState]:
        return self._drivers.get(driver_profile_id)

    def get_driver_by_user(self, user_id: int) -> Optional[DriverState]:
        driver_id = self._user_to_driver.get(user_id)
        return self._drivers.get(driver_id)

    def sync_profile(self, driver_profile_id: int, classes_allowed: list[str], car_id: int | None) -> None:
        state = self._drivers.get(driver_profile_id)
        if state is None:
            return
        state.classes_allowed = set(classes_allowed)
        state.car_id = car_id

    def get_stats(self) -> dict:
        return {
            "total_registered": len(self._drivers),
            "online": sum(1 for d in self._drivers.values() if d.status == DriverStatus.ONLINE),
            "busy": sum(1 for d in self._drivers.values() if d.status == DriverStatus.BUSY),
            "offline": sum(1 for d in self._drivers.values() if d.status == DriverStatus.OFFLINE),
        }

driver_state_storage = DriverStateStorage()
