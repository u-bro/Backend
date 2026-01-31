from typing import Any, Dict
from fastapi import WebSocket, Depends
from app.backend.routers.websocket_base import BaseWebsocketRouter
from app.services.websocket_manager import manager_notifications
from app.crud.ride import ride_crud
from app.logger import logger
from app.backend.deps import get_current_user_id_ws
from app.db import async_session_maker


class NotificationWebsocketRouter(BaseWebsocketRouter):
    def setup_routes(self) -> None:
        self.router.add_api_websocket_route("/notification", self.websocket_endpoint)

    def __init__(self) -> None:
        super().__init__()
        self.register_handler("ping", self.handle_ping)

    async def websocket_endpoint(self, websocket: WebSocket, user_id: int = Depends(get_current_user_id_ws)) -> None:
        async with async_session_maker() as session:
            await self.run(websocket, user_id=user_id, session=session)

    async def on_connect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        session = context["session"]
        await manager_notifications.connect(websocket, int(user_id))
        await websocket.send_json({"type": "connected", "user_id": user_id})
        ride = await ride_crud.get_active_ride_by_client_id(session, user_id)
        if ride:
            await websocket.send_json({"type": "active_ride", "data": ride.model_dump(mode="json")})

    async def on_disconnect(self, websocket: WebSocket, **context: Any) -> None:
        user_id = context["user_id"]
        manager_notifications.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")

    async def on_error(self, websocket: WebSocket, exc: Exception, **context: Any) -> None:
        user_id = context.get("user_id")
        logger.error(f"WebSocket error for user {user_id}: {exc}")

    async def handle_ping(self, websocket: WebSocket, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        await websocket.send_json({"type": "pong"})

notification_ws_router = NotificationWebsocketRouter().router
