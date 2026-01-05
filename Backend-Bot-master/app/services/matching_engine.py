
from datetime import datetime
from typing import Any, List, Optional, Set
from dataclasses import dataclass
import logging
from app.schemas.ride import RideSchemaAcceptByDriver
from app.schemas.ride import RideSchemaFinishWithAnomaly
from app.schemas.ride import RideSchemaUpdateByDriver
from app.crud.ride import ride_crud
from app.crud.driver_profile import driver_profile_crud
from app.services.websocket_manager import manager
from app.schemas.driver_profile import DriverProfileSchema
from starlette.status import WS_1008_POLICY_VIOLATION
from fastapi import WebSocketException
from fastapi import HTTPException
from app.services.driver_tracker import (
    driver_tracker, 
    DriverState, 
    DriverStatus,
    RideClass
)

logger = logging.getLogger(__name__)


@dataclass
class RideRequest:
    ride_id: int
    client_id: int
    ride_class: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    expected_fare: Optional[float] = None
    scheduled_at: Optional[datetime] = None
    max_wait_minutes: int = 5
    search_radius_km: float = 5.0


@dataclass
class DriverMatch:
    driver_profile_id: int
    user_id: int
    distance_km: float
    eta_minutes: float 
    rating: float
    score: float 
    
    def to_dict(self) -> dict:
        return {
            "driver_profile_id": self.driver_profile_id,
            "user_id": self.user_id,
            "distance_km": round(self.distance_km, 2),
            "eta_minutes": round(self.eta_minutes, 1),
            "rating": round(self.rating, 2),
            "score": round(self.score, 3)
        }


class MatchingEngine:

    AVG_CITY_SPEED_KMH = 30
    WEIGHT_DISTANCE = 0.5  
    WEIGHT_RATING = 0.3    
    WEIGHT_FRESHNESS = 0.2  
    MAX_DISTANCE_KM = 5.0
    DEFAULT_LIMIT = 20
    
    def __init__(self):
        self.tracker = driver_tracker
        self.connected_driver_user_ids: Set[int] = set()

    def register_connected_driver(self, profile: DriverProfileSchema) -> None:
        if not getattr(profile, "approved", False):
            return

        self.connected_driver_user_ids.add(int(profile.user_id))
        classes_allowed = getattr(profile, "classes_allowed", [])
        rating_avg = getattr(profile, "rating_avg", None)
        rating = float(rating_avg) if rating_avg is not None else 5.0

        self.tracker.register_driver(
            driver_profile_id=int(profile.id),
            user_id=int(profile.user_id),
            classes_allowed=list(classes_allowed),
            rating=rating,
        )

    def unregister_connected_driver(self, user_id: int) -> None:
        self.connected_driver_user_ids.discard(int(user_id))
    
    def find_drivers(self, ride_request: RideRequest, limit: int = DEFAULT_LIMIT) -> List[DriverMatch]:
        available = self.tracker.get_available_drivers(
            ride_class=ride_request.ride_class,
            center_lat=ride_request.pickup_lat,
            center_lng=ride_request.pickup_lng,
            radius_km=ride_request.search_radius_km,
            limit=limit * 2  
        )
        
        if not available:
            logger.info(f"No available drivers for ride {ride_request.ride_id}")
            return []
        
        matches = []
        now = datetime.utcnow()
        
        for driver in available:
            distance = self.tracker._haversine_distance(
                ride_request.pickup_lat,
                ride_request.pickup_lng,
                driver.latitude,
                driver.longitude
            )
            

            eta_minutes = (distance / self.AVG_CITY_SPEED_KMH) * 60
            
            score = self._calculate_score(driver, distance, now)
            
            matches.append(DriverMatch(
                driver_profile_id=driver.driver_profile_id,
                user_id=driver.user_id,
                distance_km=distance,
                eta_minutes=eta_minutes,
                rating=driver.rating,
                score=score
            ))
        
        matches.sort(key=lambda m: -m.score)
        
        result = matches[:limit]
        logger.info(
            f"Found {len(result)} drivers for ride {ride_request.ride_id} "
            f"(class={ride_request.ride_class}, radius={ride_request.search_radius_km}km)"
        )
        
        return result
    
    def find_single_best(self, ride_request: RideRequest) -> Optional[DriverMatch]:
        matches = self.find_drivers(ride_request, limit=1)
        return matches[0] if matches else None
    
    def expand_search(self, ride_request: RideRequest, max_radius_km: float = 15.0, step_km: float = 2.5) -> List[DriverMatch]:
        original_radius = ride_request.search_radius_km
        current_radius = original_radius
        
        while current_radius <= max_radius_km:
            ride_request.search_radius_km = current_radius
            matches = self.find_drivers(ride_request)
            
            if matches:
                ride_request.search_radius_km = original_radius
                return matches
            
            current_radius += step_km
            logger.info(f"Expanding search radius to {current_radius}km for ride {ride_request.ride_id}")
        
        ride_request.search_radius_km = original_radius
        return []
    
    def get_driver_feed(self, driver_profile_id: int, rides: List[dict], limit: int = 20) -> List[dict]:
        driver = self.tracker.get_driver(driver_profile_id)
        if not driver or driver.latitude is None:
            return []
        
        relevant_rides = []
        
        for ride in rides:
            ride_class = ride.get('ride_class', ride.get('class', 'economy'))
            if not driver.has_permit(ride_class):
                continue
            
            pickup_lat = ride.get('pickup_lat')
            pickup_lng = ride.get('pickup_lng')
            
            if pickup_lat is None or pickup_lng is None:
                continue
            
            distance = self.tracker._haversine_distance(
                driver.latitude, driver.longitude,
                float(pickup_lat), float(pickup_lng)
            )
            ride_with_distance = {
                **ride,
                'distance_to_pickup_km': round(distance, 2),
                'eta_minutes': round((distance / self.AVG_CITY_SPEED_KMH) * 60, 1)
            }
            relevant_rides.append((distance, ride_with_distance))
        
        relevant_rides.sort(key=lambda x: x[0])
        
        return [r[1] for r in relevant_rides[:limit]]
    
    def _calculate_score(self, driver: DriverState, distance_km: float, now: datetime) -> float:
        distance_score = 1 / (1 + distance_km)
        
        rating_score = driver.rating / 5.0
        
        age_seconds = (now - driver.updated_at).total_seconds()
        freshness_score = max(0, 1 - (age_seconds / 300)) 
        
        score = (
            self.WEIGHT_DISTANCE * distance_score +
            self.WEIGHT_RATING * rating_score +
            self.WEIGHT_FRESHNESS * freshness_score
        )
        
        return score
    
    def get_stats(self) -> dict:
        return {
            "tracker_stats": self.tracker.get_stats(),
            "config": {
                "avg_speed_kmh": self.AVG_CITY_SPEED_KMH,
                "weights": {
                    "distance": self.WEIGHT_DISTANCE,
                    "rating": self.WEIGHT_RATING,
                    "freshness": self.WEIGHT_FRESHNESS
                }
            }
        }

    async def send_to_suitable_drivers(self, message: Any, exclude_user_id: Optional[int] = None) -> None:
        pickup_lat = message.get("pickup_lat")
        pickup_lng = message.get("pickup_lng")

        for user_id in list(self.connected_driver_user_ids):
            if exclude_user_id and user_id == exclude_user_id:
                continue

            if not self._is_suitable_driver(user_id, pickup_lat, pickup_lng, message.get('ride_class')):
                continue

            await manager.send_personal_message(user_id, {"type": "new_ride", "details": message})

    async def accept_ride(self, session, ride_id: int, user_id: int) -> None:
        driver_profile = await driver_profile_crud.get_by_user_id(session, user_id)
        if not driver_profile:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Driver profile not found")

        existing = await ride_crud.get_by_id(session, ride_id)
        if not self._is_suitable_driver(user_id, existing.pickup_lat, existing.pickup_lng, existing.ride_class):
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Driver doesn't suit the ride")

        update_obj = RideSchemaAcceptByDriver(driver_profile_id=driver_profile.id, status='accepted')
        accepted = await ride_crud.accept(session, ride_id, update_obj, user_id)
        if accepted is not None:
            return accepted

        existing = await ride_crud.get_by_id(session, ride_id)
        if existing is None:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride not found")
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride already accepted")

    async def update_ride_status(self, session, ride_id: int, user_id: int, status: str) -> None:
        status_normalized = (status or "").strip().lower()
        if status_normalized == "accepted":
            return await self.accept_ride(session, ride_id, user_id)

        driver_profile = await driver_profile_crud.get_by_user_id(session, user_id)
        if not driver_profile:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Driver profile not found")

        existing = await ride_crud.get_by_id(session, ride_id)
        if existing is None:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride not found")

        if not self._is_suitable_driver(user_id, existing.pickup_lat, existing.pickup_lng, existing.ride_class):
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Driver doesn't suit the ride")

        if status_normalized not in ("started", "canceled"):
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Unsupported status")

        if existing.driver_profile_id != driver_profile.id:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride is not assigned to this driver")

        update_obj = RideSchemaUpdateByDriver(status=status_normalized)
        try:
            updated = await ride_crud.update(session, ride_id, update_obj, user_id)
        except HTTPException as exc:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason=str(exc.detail))

        if updated is None:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride status update failed")
        return updated

    async def finish_ride(self, session, ride_id: int, user_id: int, actual_fare: Any) -> None:
        driver_profile = await driver_profile_crud.get_by_user_id(session, user_id)
        if not driver_profile:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Driver profile not found")

        existing = await ride_crud.get_by_id(session, ride_id)
        if existing is None:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride not found")

        if existing.driver_profile_id != driver_profile.id:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride is not assigned to this driver")

        is_anomaly = str(getattr(existing, "expected_fare", None)) != str(actual_fare)
        update_obj = RideSchemaFinishWithAnomaly(
            status="completed",
            completed_at=datetime.utcnow(),
            actual_fare=actual_fare,
            is_anomaly=is_anomaly,
        )
        try:
            updated = await ride_crud.update(session, ride_id, update_obj, user_id)
        except HTTPException as exc:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason=str(exc.detail))

        if updated is None:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Ride finish failed")
        return updated

    def _is_suitable_driver(self, user_id: int, pickup_lat: float, pickup_lng: float, ride_class: str):
            state = self.tracker.get_driver_by_user(user_id)
            print(ride_class)
            print(state.classes_allowed)
            if not state or not state.is_available() or state.latitude is None or state.longitude is None or ride_class not in state.classes_allowed:
                return False

            distance_km = self.tracker._haversine_distance(
                float(pickup_lat),
                float(pickup_lng),
                float(state.latitude),
                float(state.longitude),
            )
            if distance_km > self.MAX_DISTANCE_KM:
                return False
            
            return True

matching_engine = MatchingEngine()
