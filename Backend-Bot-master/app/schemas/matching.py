from typing import List, Optional
from .base import BaseSchema


class AcceptRideRequest(BaseSchema):
    driver_profile_id: int
    user_id: int


class AcceptRideResponse(BaseSchema):
    success: bool
    status: str
    ride_id: int
    message: str


class RideFeedItem(BaseSchema):
    id: int
    client_id: int
    status: str
    pickup_address: Optional[str]
    pickup_lat: Optional[float]
    pickup_lng: Optional[float]
    dropoff_address: Optional[str]
    dropoff_lat: Optional[float]
    dropoff_lng: Optional[float]
    expected_fare: Optional[float]
    distance_to_pickup_km: Optional[float]
    eta_minutes: Optional[float]


class DriverRegistration(BaseSchema):
    driver_profile_id: int
    user_id: int
    classes_allowed: List[str]
    rating: float = 5.0


class FindDriversRequest(BaseSchema):
    ride_id: int
    ride_class: str = "economy"
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    search_radius_km: float = 5.0