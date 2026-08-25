from typing import Any, Dict
from fastapi import WebSocket, Depends, WebSocketException
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services import manager_driver_feed
from app.services.driver_state_storage import driver_state_storage
from app.crud.driver_tracker import driver_tracker, DriverStatus
from app.crud import driver_feed
from app.logger import logger
from app.backend.deps import get_current_user_id_ws
from app.db import async_session_maker
from app.crud import driver_profile_crud, ride_drivers_request_crud, ride_crud
from starlette.status import WS_1008_POLICY_VIOLATION
from app.const import ACTIVE_RIDE_STATUSES
from app.models import Ride
from sqlalchemy import select
from app.services.after_commit import add_after_commit


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

        await driver_feed.stop_feed(user_id)

    async def websocket_endpoint(self, websocket: WebSocket, user_id: int = Depends(get_current_user_id_ws)) -> None:
        async with async_session_maker() as session:
            await self.run(websocket, user_id=user_id, session=session)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        session = context["session"]
        driver_profile = await driver_profile_crud.get_by_user_id(session, int(user_id))
        if driver_profile is None or not getattr(driver_profile, "approved", False):
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION, reason="Not a driver")

        state = await driver_state_storage.register_driver(session, driver_profile)
        await manager_driver_feed.connect(websocket, int(user_id))
        await websocket.send_json({"type": "connected", "user_id": user_id})
        

        active_ride_id = await session.scalar(select(Ride.id).where(Ride.driver_profile_id == driver_profile.id, Ride.status.in_(ACTIVE_RIDE_STATUSES)).limit(1))
        pending = await ride_drivers_request_crud.get_requested_with_ride_by_driver_profile_id(session, driver_profile.id)
        authoritative_status = DriverStatus.BUSY if active_ride_id else DriverStatus.OFFLINE if state.status == DriverStatus.OFFLINE else DriverStatus.WAITING_RIDE if pending else DriverStatus.ONLINE
        if state.status != authoritative_status:
            await driver_tracker.set_status_by_driver(session, driver_profile.id, authoritative_status)

        if authoritative_status in (DriverStatus.ONLINE, DriverStatus.WAITING_RIDE):
            add_after_commit(session, lambda: driver_feed.start_feed_task(user_id=int(user_id), driver_profile_id=int(driver_profile.id)))

        if authoritative_status == DriverStatus.BUSY:
            ride = await ride_crud.get_active_ride_by_driver_profile_id(session, driver_profile.id)
            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "active_ride", "data": ride.model_dump(mode="json") if ride else None})

        if pending:
            data = [item.model_dump(mode="json") for item in pending]
            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "pending_rides", "data": data})
            for item in data:
                await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "waiting_ride", "data": item})
        else:
            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "pending_rides", "data": []})

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = int(context["user_id"])
        manager_driver_feed.disconnect(websocket, user_id)
        await self._stop_feed_task_if_last_connection(int(user_id))
        logger.info(f"User {user_id} disconnected")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"WebSocket error for user {user_id}: {exc}")

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

    async def handle_location_update(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = context["user_id"]
        lat = data.get("lat") if data.get("lat") is not None else data.get("latitude")
        lng = data.get("lng") if data.get("lng") is not None else data.get("longitude")

        if lat is not None and lng is not None:
            state = await driver_tracker.update_location_by_user_id(session, user_id=user_id, latitude=float(lat), longitude=float(lng))
            if state:
                await websocket.send_json({"type": "location_ack", "status": state.status})

    async def handle_go_online(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = int(context["user_id"])
        old_state = driver_state_storage.get_driver_by_user(user_id)
        if old_state.status != DriverStatus.ONLINE and old_state.status != DriverStatus.OFFLINE and old_state.status != DriverStatus.WAITING_RIDE:
            await manager_driver_feed.send_personal_message(old_state.user_id, {"type": "error", "message": "Водитель занят, статус не может быть изменен"})
            return None

        pending = await ride_drivers_request_crud.get_requested_by_driver_profile_id(session, old_state.driver_profile_id)
        status = DriverStatus.WAITING_RIDE if pending else DriverStatus.ONLINE
        state = await driver_tracker.set_status_by_user(session, user_id, status)
        if state:
            await websocket.send_json({"type": "status_changed", "status": "online"})

    async def handle_go_offline(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        session = context["session"]
        user_id = int(context["user_id"])
        old_state = driver_state_storage.get_driver_by_user(user_id)
        if old_state.status != DriverStatus.ONLINE and old_state.status != DriverStatus.OFFLINE and old_state.status != DriverStatus.WAITING_RIDE:
            await manager_driver_feed.send_personal_message(old_state.user_id, {"type": "error", "message": "Водитель занят, статус не может быть изменен"})
            return None

        await ride_drivers_request_crud.cancel_by_driver_profile_id(session, old_state.driver_profile_id, "driver_offline")

        await driver_tracker.set_status_by_user(session, user_id, DriverStatus.OFFLINE)
        await websocket.send_json({"type": "status_changed", "status": "offline"})

matching_ws_router = MatchingWebsocketRouter().router
