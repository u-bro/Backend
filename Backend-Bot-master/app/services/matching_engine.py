
from datetime import datetime
from typing import Any, List, Optional, Set
from dataclasses import dataclass
import logging

from app.services.websocket_manager import manager
from app.schemas.driver_profile import DriverProfileSchema
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
        classes_allowed = getattr(profile, "classes_allowed", None) or ["economy"]
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
        payload: Any = message

        pickup_lat = payload.get("pickup_lat")
        pickup_lng = payload.get("pickup_lng")

        max_distance_km = self.MAX_DISTANCE_KM
        for user_id in list(self.connected_driver_user_ids):
            if exclude_user_id and int(user_id) == int(exclude_user_id):
                continue

            state = self.tracker.get_driver_by_user(int(user_id))
            if not state or not state.is_available() or state.latitude is None or state.longitude is None:
                continue

            distance_km = self.tracker._haversine_distance(
                float(pickup_lat),
                float(pickup_lng),
                float(state.latitude),
                float(state.longitude),
            )
            if distance_km > max_distance_km:
                continue

            await manager.send_personal_message(int(user_id), payload)

matching_engine = MatchingEngine()
