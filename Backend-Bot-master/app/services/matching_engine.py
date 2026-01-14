from typing import Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.websocket_manager import manager
from app.schemas.driver_profile import DriverProfileSchema
from app.crud.driver_tracker import driver_tracker
from app.config import MAX_DISTANCE_KM

class MatchingEngine:
    AVG_CITY_SPEED_KMH = 30
    
    def __init__(self):
        self.tracker = driver_tracker
        self.connected_driver_user_ids: Set[int] = set()

    async def register_connected_driver(self, session: AsyncSession, profile: DriverProfileSchema) -> None:
        if not getattr(profile, "approved", False):
            return

        self.connected_driver_user_ids.add(int(profile.user_id))
        await self.tracker.register_driver(session, profile)

    def unregister_connected_driver(self, user_id: int) -> None:
        self.connected_driver_user_ids.discard(int(user_id))
    
    def get_stats(self) -> dict:
        return {"tracker_stats": self.tracker.get_stats()}

    async def send_to_suitable_drivers(self, message: dict, exclude_user_id: Optional[int] = None) -> None:
        pickup_lat = message.get("pickup_lat")
        pickup_lng = message.get("pickup_lng")

        for user_id in list(self.connected_driver_user_ids):
            if exclude_user_id and user_id == exclude_user_id:
                continue

            if not self._is_suitable_driver(user_id, pickup_lat, pickup_lng, message.get('ride_class')):
                continue

            await manager.send_personal_message(user_id, {"type": "new_ride", "details": message})

    def _is_suitable_driver(self, user_id: int, pickup_lat: float, pickup_lng: float, ride_class: str):
            state = self.tracker.get_driver_by_user(user_id)
            if not state or not state.is_available() or state.latitude is None or state.longitude is None or ride_class not in state.classes_allowed:
                return False

            distance_km = self.tracker._haversine_distance(
                float(pickup_lat),
                float(pickup_lng),
                float(state.latitude),
                float(state.longitude),
            )
            if distance_km > MAX_DISTANCE_KM:
                return False
            
            return True

matching_engine = MatchingEngine()
