from typing import Any, Dict, Optional
from fastapi import HTTPException, Query, WebSocket
from pydantic import BaseModel
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services.websocket_manager import manager
from app.services.driver_tracker import driver_tracker, DriverStatus
from app.logger import logger

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy_m: Optional[int] = None


class DriverStatusUpdate(BaseModel):
    status: str 


class DriverWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/ws/{user_id}", self.websocket_endpoint)

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
        self.register_handler("join_ride", self.handle_join_ride)
        self.register_handler("leave_ride", self.handle_leave_ride)
        self.register_handler("chat_message", self.handle_chat_message)
        self.register_handler("location_update", self.handle_location_update)
        self.register_handler("go_online", self.handle_go_online)
        self.register_handler("go_offline", self.handle_go_offline)
        self.register_handler("pause", self.handle_pause)

    async def websocket_endpoint(self, websocket: WebSocket, user_id: int, token: Optional[str] = Query(None)) -> None:
        await self.run(websocket, user_id=user_id, token=token)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = int(context["user_id"])

        # TODO:
        await manager.connect(websocket, user_id)

        await websocket.send_json(
            {
                "type": "connected",
                "user_id": user_id,
                "message": "WebSocket connection established",
            }
        )

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = int(context["user_id"])
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"WebSocket error for user {user_id}: {exc}")

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

    async def handle_join_ride(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        ride_id = data.get("ride_id")
        if ride_id:
            manager.join_ride(ride_id, user_id)
            await websocket.send_json({"type": "joined_ride", "ride_id": ride_id})

    async def handle_leave_ride(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        ride_id = data.get("ride_id")
        if ride_id:
            manager.leave_ride(ride_id, user_id)
            await websocket.send_json({"type": "left_ride", "ride_id": ride_id})

    async def handle_chat_message(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        ride_id = data.get("ride_id")
        text = data.get("text")
        if ride_id and text:
            await manager.send_to_ride(
                ride_id,
                {
                    "type": "chat_message",
                    "ride_id": ride_id,
                    "sender_id": user_id,
                    "text": text,
                },
            )

    async def handle_location_update(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        lat = data.get("lat") or data.get("latitude")
        lng = data.get("lng") or data.get("longitude")
        ride_id = data.get("ride_id")
        heading = data.get("heading")
        speed = data.get("speed")

        if lat and lng:
            state = driver_tracker.update_location_by_user(
                user_id=user_id,
                latitude=float(lat),
                longitude=float(lng),
                heading=heading,
                speed=speed,
            )

            if state:
                await websocket.send_json({"type": "location_ack", "status": state.status.value})

            if ride_id:
                await manager.send_to_ride(
                    ride_id,
                    {
                        "type": "driver_location",
                        "ride_id": ride_id,
                        "driver_id": user_id,
                        "lat": lat,
                        "lng": lng,
                        "heading": heading,
                        "speed": speed,
                    },
                    exclude_user_id=user_id,
                )

    async def handle_go_online(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.ONLINE)
        if state:
            await websocket.send_json(
                {
                    "type": "status_changed",
                    "status": "online",
                    "message": "Вы на линии, ожидайте заказы",
                }
            )

    async def handle_go_offline(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.OFFLINE)
        if state:
            await websocket.send_json(
                {
                    "type": "status_changed",
                    "status": "offline",
                    "message": "Вы оффлайн",
                }
            )

    async def handle_pause(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        user_id = int(context["user_id"])

        state = driver_tracker.set_status_by_user(user_id, DriverStatus.PAUSED)
        if state:
            await websocket.send_json(
                {
                    "type": "status_changed",
                    "status": "paused",
                    "message": "Вы на паузе",
                }
            )

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
        state = driver_tracker.update_location_by_user(
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


websocket_router = DriverWebsocketRouter().router
