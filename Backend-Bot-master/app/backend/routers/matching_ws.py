from typing import Any, Dict, Optional
from fastapi import HTTPException, Query, WebSocket, Depends
from pydantic import BaseModel
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services.websocket_manager import manager
from app.services.driver_tracker import driver_tracker, DriverStatus
from app.logger import logger
from app.backend.deps import get_current_user_id_ws
from app.db import async_session_maker
from app.crud.ride import ride_crud
from app.schemas.ride import RideSchemaCreate
from app.crud.driver_profile import driver_profile_crud
from app.services.matching_engine import matching_engine
from datetime import datetime


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy_m: Optional[int] = None


class DriverStatusUpdate(BaseModel):
    status: str 


class MatchingWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/ws", self.websocket_endpoint)

        self.router.add_api_route("/ws/stats", self.get_websocket_stats, methods=["GET"])
        self.router.add_api_route("/ws/notify/{user_id}", self.send_notification, methods=["POST"])
        self.router.add_api_route("/ws/broadcast", self.broadcast_message, methods=["POST"])
        self.router.add_api_route("/ws/driver/{user_id}/location", self.update_driver_location, methods=["POST"])
        self.router.add_api_route("/ws/driver/{user_id}/status", self.update_driver_status, methods=["POST"])
        self.router.add_api_route("/ws/driver/{user_id}/state", self.get_driver_state, methods=["GET"])
        self.router.add_api_route("/ws/drivers/stats", self.get_drivers_stats, methods=["GET"])

    def __init__(self) -> None:
        super().__init__()

        self.register_handler("ping", self.handle_ping)
        self.register_handler("create_ride", self.handle_create_ride)
        self.register_handler("accept_ride", self.handle_accept_ride)
        self.register_handler("update_ride_status", self.handle_update_ride_status)
        self.register_handler("finish_ride", self.handle_finish_ride)
        self.register_handler("location_update", self.handle_location_update)
        self.register_handler("go_online", self.handle_go_online)
        self.register_handler("go_offline", self.handle_go_offline)
        self.register_handler("pause", self.handle_pause)

    async def websocket_endpoint(self, websocket: WebSocket, user_id: int = Depends(get_current_user_id_ws)) -> None:
        async with async_session_maker() as session:
            await self.run(websocket, user_id=user_id, session=session)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        session = context["session"]
        driver_profile = await driver_profile_crud.get_by_user_id(session, int(user_id))
        if driver_profile is not None and getattr(driver_profile, "approved", False):
            matching_engine.register_connected_driver(driver_profile)

        await manager.connect(websocket, int(user_id))

        await websocket.send_json(
            {
                "type": "connected",
                "user_id": user_id,
                "message": "WebSocket connection established",
            }
        )

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        matching_engine.unregister_connected_driver(int(user_id))
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"WebSocket error for user {user_id}: {exc}")

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

    async def handle_create_ride(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        ride_details = data.get("details", {})
        create_obj = RideSchemaCreate(client_id=user_id, **ride_details)
        ride_schema = await ride_crud.create(session, create_obj)
        await session.commit()

        ride_dict = self._ride_schema_to_dict(ride_schema)
        await matching_engine.send_to_suitable_drivers(ride_dict)

        await websocket.send_json({"type": "ride_created", "message": ride_dict})

    async def handle_accept_ride(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        ride_id = data.get("ride_id", 0)
        ride_schema = await matching_engine.accept_ride(session, ride_id, user_id)
        ride_dict = self._ride_schema_to_dict(ride_schema)
        await websocket.send_json({"type": "ride_accepted", "details": ride_dict})
        await manager.send_personal_message(ride_dict.get("client_id"), {"type": "ride_accepted", "details": ride_dict})

    async def handle_update_ride_status(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        ride_id = data.get("ride_id", 0)
        status = data.get("status")
        ride_schema = await matching_engine.update_ride_status(session, ride_id, user_id, status)
        ride_dict = self._ride_schema_to_dict(ride_schema)
        await websocket.send_json({"type": "ride_status_changed", "details": ride_dict})
        await manager.send_personal_message(ride_dict.get("client_id"), {"type": "ride_status_changed", "details": ride_dict})

    async def handle_finish_ride(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        ride_id = data.get("ride_id", 0)
        actual_fare = data.get("actual_fare")
        ride_schema = await matching_engine.finish_ride(session, ride_id, user_id, actual_fare)
        ride_dict = self._ride_schema_to_dict(ride_schema)
        await websocket.send_json({"type": "ride_status_changed", "details": ride_dict})
        await manager.send_personal_message(ride_dict.get("client_id"), {"type": "ride_status_changed", "details": ride_dict})


    async def handle_location_update(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = context["user_id"]
        lat = data.get("lat") or data.get("latitude")
        lng = data.get("lng") or data.get("longitude")
        heading = data.get("heading")
        speed = data.get("speed")

        if lat and lng:
            state = driver_tracker.update_location_by_user_id(user_id=user_id, latitude=float(lat), longitude=float(lng), heading=heading, speed=speed)
            if state:
                await websocket.send_json({"type": "location_ack", "status": state.status.value})


    async def handle_go_online(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.ONLINE)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "online"})

    async def handle_go_offline(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.OFFLINE)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "offline"})

    async def handle_pause(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.PAUSED)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "paused"})

    async def get_websocket_stats(self) -> Dict[str, Any]:
        return {
            "online_users": manager.get_online_users(),
            "total_connections": manager.get_connection_count(),
            "active_rides": list(manager.ride_participants.keys()),
        }

    async def send_notification(self, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
        if not manager.is_connected(user_id):
            raise HTTPException(status_code=404, detail="User not connected")

        await manager.send_personal_message(
            user_id,
            {
                "type": "notification",
                **message,
            },
        )

        return {"status": "sent", "user_id": user_id}

    async def broadcast_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        await manager.broadcast({"type": "broadcast", **message})
        return {"status": "broadcasted", "recipients": manager.get_connection_count()}

    async def update_driver_location(self, user_id: int, location: LocationUpdate) -> Dict[str, Any]:
        state = driver_tracker.update_location_by_user_id(
            user_id=user_id,
            latitude=location.latitude,
            longitude=location.longitude,
            heading=location.heading,
            speed=location.speed,
            accuracy_m=location.accuracy_m,
        )

        if not state:
            raise HTTPException(status_code=404, detail="Driver not registered in tracker")

        return {
            "status": "updated",
            "driver_status": state.status.value,
            "location": {"lat": state.latitude, "lng": state.longitude},
        }

    async def update_driver_status(self, user_id: int, status_update: DriverStatusUpdate) -> Dict[str, Any]:
        try:
            status = DriverStatus(status_update.status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Allowed: {[s.value for s in DriverStatus]}",
            )

        state = driver_tracker.set_status_by_user(user_id, status)

        if not state:
            raise HTTPException(status_code=404, detail="Driver not registered in tracker")

        return {"status": "updated", "driver_status": state.status.value}

    async def get_driver_state(self, user_id: int) -> Dict[str, Any]:
        state = driver_tracker.get_driver_by_user(user_id)

        if not state:
            raise HTTPException(status_code=404, detail="Driver not found in tracker")

        return {
            "driver_profile_id": state.driver_profile_id,
            "user_id": state.user_id,
            "status": state.status.value,
            "is_available": state.is_available(),
            "location": {
                "lat": state.latitude,
                "lng": state.longitude,
                "heading": state.heading,
                "speed": state.speed,
            }
            if state.latitude
            else None,
            "current_ride_id": state.current_ride_id,
            "classes_allowed": list(state.classes_allowed),
            "rating": state.rating,
            "updated_at": state.updated_at.isoformat(),
        }

    async def get_drivers_stats(self) -> Dict[str, Any]:
        return {**driver_tracker.get_stats(), "ws_connections": manager.get_connection_count()}

    def _ride_schema_to_dict(self, ride_schema):
        ride_dict = ride_schema.model_dump()
        def convert_datetimes(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, dict):
                return {k: convert_datetimes(v) for k, v in value.items()}
            if isinstance(value, list):
                return [convert_datetimes(v) for v in value]
            if isinstance(value, tuple):
                return tuple(convert_datetimes(v) for v in value)
            return value

        return convert_datetimes(ride_dict)

matching_ws_router = MatchingWebsocketRouter().router
