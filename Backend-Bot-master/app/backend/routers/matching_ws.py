from typing import Any, Dict
from fastapi import WebSocket, Depends
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services.websocket_manager import manager
from app.services.driver_tracker import driver_tracker, DriverStatus
from app.logger import logger
from app.backend.deps import get_current_user_id_ws
from app.db import async_session_maker
from app.crud.driver_profile import driver_profile_crud
from app.services.matching_engine import matching_engine


class MatchingWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/ws", self.websocket_endpoint)

    def __init__(self) -> None:
        super().__init__()

        self.register_handler("ping", self.handle_ping)
        self.register_handler("location_update", self.handle_location_update)
        self.register_handler("go_online", self.handle_go_online)
        self.register_handler("go_offline", self.handle_go_offline)

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

        await websocket.send_json({"type": "connected", "user_id": user_id})

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

matching_ws_router = MatchingWebsocketRouter().router
