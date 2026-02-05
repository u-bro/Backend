from typing import Dict
from asyncio import Task
import asyncio, logging
from app.services.websocket_manager import manager_notifications
from app.db import async_session_maker
from .driver_location import driver_location_crud
from app.config import DRIVER_LOCATION_PUSH_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


class DriverLocationSender:
    def __init__(self):
        self._tasks: Dict[int, Task[None]] = {}

    async def start_task(self, user_id: int, driver_profile_id: int) -> None:
        existing = self._tasks.get(user_id)
        if existing is not None and not existing.done():
            existing.cancel()

        self._tasks[user_id] = asyncio.create_task(self._loop(user_id=user_id, driver_profile_id=driver_profile_id))

    async def stop_task(self, user_id: int) -> None:
        task = self._tasks.pop(user_id, None)
        if task is None:
            return

        if not task.done():
            task.cancel()

    async def _loop(self, user_id: int, driver_profile_id: int) -> None:
        try:
            while manager_notifications.is_connected(user_id):
                async with async_session_maker() as session:
                    location = await driver_location_crud.get_by_driver_profile_id(session, driver_profile_id)
                    await manager_notifications.send_personal_message(user_id, {"type": "driver_location", "location": location.model_dump(mode='json')})

                await asyncio.sleep(DRIVER_LOCATION_PUSH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error(f"Driver location loop error for user {user_id}: {exc}")

driver_location_sender = DriverLocationSender()