from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging
from datetime import datetime, timezone
from app.crud import user_crud
from sqlalchemy.ext.asyncio import AsyncSession
from .fcm_service import fcm_service
from app.schemas.push import PushNotificationData

logger = logging.getLogger(__name__)


class ConnectionManager:
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.ride_participants: Dict[int, set] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: user_id={user_id}, total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected: user_id={user_id}")

    def is_connected(self, user_id: int) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_personal_message(self, user_id: int, message: dict) -> bool:
        connections = self.active_connections.get(user_id)
        if not connections:
            logger.warning(f"User {user_id} is not connected")
            return False

        message_with_timestamp = {
            **self.convert_datetime_to_str_in_dict(message),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        alive: list[WebSocket] = []
        delivered = False

        for ws in list(connections):
            try:
                await ws.send_json(message_with_timestamp)
                alive.append(ws)
                delivered = True
            except (RuntimeError, WebSocketDisconnect) as exc:
                logger.warning(f"WS send failed user_id={user_id}: {exc}")
            except Exception as exc:
                logger.warning(f"WS send failed user_id={user_id} unexpected: {exc}")

        if alive:
            self.active_connections[user_id] = alive
        else:
            self.active_connections.pop(user_id, None)

        return delivered
    
    async def broadcast(self, message: dict, exclude_user_id: Optional[int] = None) -> None:
        message_with_timestamp = {
            **self.convert_datetime_to_str_in_dict(message),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for user_id, connections in self.active_connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            for websocket in connections:
                await websocket.send_json(message_with_timestamp)
    
    def join_ride(self, ride_id: int, user_id: int) -> None:
        if ride_id not in self.ride_participants:
            self.ride_participants[ride_id] = set()
        self.ride_participants[ride_id].add(user_id)
        logger.info(f"User {user_id} joined ride {ride_id}")
    
    def leave_ride(self, ride_id: int, user_id: int) -> None:
        if ride_id in self.ride_participants:
            self.ride_participants[ride_id].discard(user_id)
            if not self.ride_participants[ride_id]:
                del self.ride_participants[ride_id]
        logger.info(f"User {user_id} left ride {ride_id}")
    
    async def send_to_ride(self, session: AsyncSession, ride_id: int, message: dict, exclude_user_id: Optional[int] = None, my_user_id: Optional[int] = None) -> None:
        if ride_id not in self.ride_participants:
            logger.warning(f"No participants in ride {ride_id}")
            return

        for user_id in self.ride_participants[ride_id]:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            new_message = message.copy()
            if new_message.get('type', '') == 'new_message': 
                new_message['message'] = message['message'].copy()
                if my_user_id and user_id == my_user_id:    
                    new_message['message']['message_type'] = 'me'

            await self.send_personal_message(user_id, new_message)
            sender_id = new_message.get('message', {}).get('sender_id', 0)
            if new_message.get('type', '') == 'new_message' and sender_id != user_id:
                sender = await user_crud.get_by_id(session, sender_id)
                sender_fullname = " ".join([word for word in [sender.last_name, sender.first_name] if word])
                await fcm_service.send_to_user(session, user_id, PushNotificationData(title=sender_fullname, body=new_message.get('message', {}).get('text', 'TEXT')))

    def get_online_users(self) -> List[int]:
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    def convert_datetime_to_str_in_dict(self, dictionary):
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

        return convert_datetimes(dictionary)

manager = ConnectionManager()
manager_driver_feed = ConnectionManager()
manager_notifications = ConnectionManager()
