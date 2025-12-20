from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional, List

from app.crud.ride import ride_crud
from app.crud.driver_profile import driver_profile_crud
from app.services.driver_tracker import driver_tracker, DriverStatus
from app.services.matching_engine import matching_engine, RideRequest, DriverMatch
from app.services.websocket_manager import manager

router = APIRouter()

class AcceptRideRequest(BaseModel):
    driver_profile_id: int
    user_id: int 


class AcceptRideResponse(BaseModel):
    success: bool
    status: str  
    ride_id: int
    message: str


class RideFeedItem(BaseModel):
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


class DriverRegistration(BaseModel):
    driver_profile_id: int
    user_id: int
    classes_allowed: List[str]
    rating: float = 5.0


class FindDriversRequest(BaseModel):
    ride_id: int
    ride_class: str = "economy"
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    search_radius_km: float = 5.0


@router.post("/matching/driver/register")
async def register_driver(
    request: Request,
    data: DriverRegistration,
):
    profile = await driver_profile_crud.get_by_id(request.state.session, data.driver_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    state = driver_tracker.register_driver(
        driver_profile_id=data.driver_profile_id,
        user_id=data.user_id,
        classes_allowed=data.classes_allowed,
        rating=data.rating
    )
    
    return {
        "status": "registered",
        "driver_profile_id": state.driver_profile_id,
        "classes_allowed": list(state.classes_allowed)
    }


@router.get("/matching/feed/{driver_profile_id}")
async def get_ride_feed(
    request: Request,
    driver_profile_id: int,
    limit: int = Query(20, ge=1, le=100),
):
    driver = driver_tracker.get_driver(driver_profile_id)
    if not driver:
        raise HTTPException(
            status_code=400, 
            detail="Driver not registered in tracker. Call POST /matching/driver/register first"
        )
    
    if driver.latitude is None:
        raise HTTPException(
            status_code=400,
            detail="Driver location not set. Send location_update via WebSocket"
        )
    pending_rides = await ride_crud.get_pending_rides(request.state.session, limit=limit * 2)
    rides_dict = [
        {
            "id": r.id,
            "client_id": r.client_id,
            "status": r.status,
            "pickup_address": r.pickup_address,
            "pickup_lat": r.pickup_lat,
            "pickup_lng": r.pickup_lng,
            "dropoff_address": r.dropoff_address,
            "dropoff_lat": r.dropoff_lat,
            "dropoff_lng": r.dropoff_lng,
            "expected_fare": r.expected_fare,
            "ride_class": "economy",  # TODO: добавить поле в модель
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in pending_rides
        if r.pickup_lat and r.pickup_lng
    ]
    feed = matching_engine.get_driver_feed(driver_profile_id, rides_dict, limit)
    
    return {
        "driver_profile_id": driver_profile_id,
        "driver_status": driver.status.value,
        "count": len(feed),
        "rides": feed
    }


@router.post("/matching/accept/{ride_id}", response_model=AcceptRideResponse)
async def accept_ride(
    request: Request,
    ride_id: int,
    data: AcceptRideRequest,
):
    ride, status = await ride_crud.accept_ride_idempotent(
        session=request.state.session,
        ride_id=ride_id,
        driver_profile_id=data.driver_profile_id,
        actor_id=data.user_id
    )
    
    success = status in ("accepted", "already_yours")
    
    messages = {
        "accepted": "Заказ успешно принят!",
        "already_yours": "Этот заказ уже был принят вами",
        "already_taken": "Заказ уже принят другим водителем",
        "not_found": "Заказ не найден",
        "invalid_status": "Заказ недоступен для принятия"
    }
    
    if success:
        driver_tracker.assign_ride(data.driver_profile_id, ride_id)
        if ride:
            await manager.send_personal_message(ride.client_id, {
                "type": "ride_accepted",
                "ride_id": ride_id,
                "driver_profile_id": data.driver_profile_id,
                "message": "Водитель принял ваш заказ!"
            })
        
        await request.state.session.commit()
    
    return AcceptRideResponse(
        success=success,
        status=status,
        ride_id=ride_id,
        message=messages.get(status, "Unknown status")
    )


@router.post("/matching/find-drivers")
async def find_drivers_for_ride(
    data: FindDriversRequest,
    limit: int = Query(10, ge=1, le=50)
):
    request = RideRequest(
        ride_id=data.ride_id,
        client_id=0, 
        ride_class=data.ride_class,
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        dropoff_lat=data.dropoff_lat,
        dropoff_lng=data.dropoff_lng,
        search_radius_km=data.search_radius_km
    )
    
    drivers = matching_engine.find_drivers(request, limit=limit)
    
    return {
        "ride_id": data.ride_id,
        "ride_class": data.ride_class,
        "search_radius_km": data.search_radius_km,
        "found": len(drivers),
        "drivers": [d.to_dict() for d in drivers]
    }


@router.get("/matching/stats")
async def get_matching_stats():
    return matching_engine.get_stats()


matching_router = router
