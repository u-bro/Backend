from typing import Any, Dict
from fastapi import WebSocket, Depends, WebSocketException
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services.websocket_manager import manager_driver_feed
from app.crud.driver_tracker import driver_tracker, DriverStatus
from app.services.matching_engine import matching_engine
from app.logger import logger
from app.backend.deps import get_current_user_id_ws
from app.db import async_session_maker
from app.crud.driver_profile import driver_profile_crud
from starlette.status import WS_1008_POLICY_VIOLATION


class MatchingWebsocketRouter(BaseWebsocketRouter):

    def __init__(self) -> None:
        super().__init__()
        self.register_handler("ping", self.handle_ping)
        self.register_handler("location_update", self.handle_location_update)
        self.register_handler("go_online", self.handle_go_online)
        self.register_handler("go_offline", self.handle_go_offline)

    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/ws", self.websocket_endpoint)

    async def _stop_feed_task_if_last_connection(self, user_id: int) -> None:
        if manager_driver_feed.is_connected(user_id):
            return

        await driver_tracker.stop_feed(user_id)

    async def websocket_endpoint(self, websocket: WebSocket, user_id: int = Depends(get_current_user_id_ws)) -> None:
        async with async_session_maker() as session:
            await self.run(websocket, user_id=user_id, session=session)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        session = context["session"]
        driver_profile = await driver_profile_crud.get_by_user_id(session, int(user_id))
        if driver_profile is None or not getattr(driver_profile, "approved", False):
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Not a driver")

        await matching_engine.register_connected_driver(session, driver_profile)
        await manager_driver_feed.connect(websocket, int(user_id))

        await websocket.send_json({"type": "connected", "user_id": user_id})

        await driver_tracker.start_feed_task(user_id=int(user_id), driver_profile_id=int(driver_profile.id))

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        manager_driver_feed.disconnect(websocket, user_id)
        await self._stop_feed_task_if_last_connection(int(user_id))

        if not manager_driver_feed.is_connected(int(user_id)):
            matching_engine.unregister_connected_driver(int(user_id))
        logger.info(f"User {user_id} disconnected")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"WebSocket error for user {user_id}: {exc}")

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

    async def handle_location_update(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        lat = data.get("lat") or data.get("latitude")
        lng = data.get("lng") or data.get("longitude")

        if lat and lng:
            state = await driver_tracker.update_location_by_user_id(session, user_id=user_id, latitude=float(lat), longitude=float(lng))
            if state:
                await websocket.send_json({"type": "location_ack", "status": state.status.value})

    async def handle_go_online(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = int(context["user_id"])
        state = await driver_tracker.set_status_by_user(session, user_id, DriverStatus.ONLINE)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "online"})

    async def handle_go_offline(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = int(context["user_id"])
        state = await driver_tracker.set_status_by_user(session, user_id, DriverStatus.OFFLINE)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "offline"})

matching_ws_router = MatchingWebsocketRouter().router
