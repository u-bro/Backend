"""
WebSocket Router
Обработка WebSocket соединений для real-time функционала
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
import json
import logging

from app.services.websocket_manager import manager
from app.services.driver_tracker import driver_tracker, DriverStatus

logger = logging.getLogger(__name__)


# === Pydantic модели для HTTP эндпоинтов ===

class LocationUpdate(BaseModel):
    """Обновление локации водителя"""
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy_m: Optional[int] = None


class DriverStatusUpdate(BaseModel):
    """Обновление статуса водителя"""
    status: str  # online, offline, busy, paused

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Optional[str] = Query(None)
):
    """
    Основной WebSocket эндпоинт.
    
    Подключение: ws://localhost:5000/api/v1/ws/{user_id}?token=xxx
    
    Форматы сообщений:
    
    1. Подписка на поездку:
       {"type": "join_ride", "ride_id": 123}
    
    2. Отписка от поездки:
       {"type": "leave_ride", "ride_id": 123}
    
    3. Отправка сообщения в чат поездки:
       {"type": "chat_message", "ride_id": 123, "text": "Привет!"}
    
    4. Обновление локации водителя:
       {"type": "location_update", "lat": 55.7558, "lng": 37.6173}
    
    5. Ping для поддержания соединения:
       {"type": "ping"}
    """
    
    # TODO: Валидация токена
    # if not await validate_token(token, user_id):
    #     await websocket.close(code=4001, reason="Invalid token")
    #     return
    
    await manager.connect(websocket, user_id)
    
    try:
        # Отправляем подтверждение подключения
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "WebSocket connection established"
        })
        
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_json()
            
            await handle_message(websocket, user_id, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


async def handle_message(websocket: WebSocket, user_id: int, data: dict) -> None:
    """Обработка входящих WebSocket сообщений"""
    
    message_type = data.get("type")
    
    if message_type == "ping":
        await websocket.send_json({"type": "pong"})
    
    elif message_type == "join_ride":
        ride_id = data.get("ride_id")
        if ride_id:
            manager.join_ride(ride_id, user_id)
            await websocket.send_json({
                "type": "joined_ride",
                "ride_id": ride_id
            })
    
    elif message_type == "leave_ride":
        ride_id = data.get("ride_id")
        if ride_id:
            manager.leave_ride(ride_id, user_id)
            await websocket.send_json({
                "type": "left_ride",
                "ride_id": ride_id
            })
    
    elif message_type == "chat_message":
        ride_id = data.get("ride_id")
        text = data.get("text")
        if ride_id and text:
            # Отправляем сообщение всем участникам поездки
            await manager.send_to_ride(ride_id, {
                "type": "chat_message",
                "ride_id": ride_id,
                "sender_id": user_id,
                "text": text
            })
    
    elif message_type == "location_update":
        # Обновление локации водителя
        lat = data.get("lat") or data.get("latitude")
        lng = data.get("lng") or data.get("longitude")
        ride_id = data.get("ride_id")
        heading = data.get("heading")
        speed = data.get("speed")
        
        if lat and lng:
            # Обновляем в DriverTracker
            state = driver_tracker.update_location_by_user(
                user_id=user_id,
                latitude=float(lat),
                longitude=float(lng),
                heading=heading,
                speed=speed
            )
            
            if state:
                await websocket.send_json({
                    "type": "location_ack",
                    "status": state.status.value
                })
            
            # Если есть ride_id - отправляем клиенту обновление
            if ride_id:
                await manager.send_to_ride(ride_id, {
                    "type": "driver_location",
                    "ride_id": ride_id,
                    "driver_id": user_id,
                    "lat": lat,
                    "lng": lng,
                    "heading": heading,
                    "speed": speed
                }, exclude_user_id=user_id)
    
    elif message_type == "go_online":
        # Водитель выходит на линию
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.ONLINE)
        if state:
            await websocket.send_json({
                "type": "status_changed",
                "status": "online",
                "message": "Вы на линии, ожидайте заказы"
            })
    
    elif message_type == "go_offline":
        # Водитель уходит с линии
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.OFFLINE)
        if state:
            await websocket.send_json({
                "type": "status_changed", 
                "status": "offline",
                "message": "Вы оффлайн"
            })
    
    elif message_type == "pause":
        # Временная пауза
        state = driver_tracker.set_status_by_user(user_id, DriverStatus.PAUSED)
        if state:
            await websocket.send_json({
                "type": "status_changed",
                "status": "paused",
                "message": "Вы на паузе"
            })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


# === HTTP эндпоинты для управления ===

@router.get("/ws/stats")
async def get_websocket_stats():
    """Статистика WebSocket соединений"""
    return {
        "online_users": manager.get_online_users(),
        "total_connections": manager.get_connection_count(),
        "active_rides": list(manager.ride_participants.keys())
    }


@router.post("/ws/notify/{user_id}")
async def send_notification(user_id: int, message: dict):
    """
    Отправка уведомления пользователю через WebSocket.
    Используется другими сервисами для push-уведомлений.
    """
    if not manager.is_connected(user_id):
        raise HTTPException(status_code=404, detail="User not connected")
    
    await manager.send_personal_message(user_id, {
        "type": "notification",
        **message
    })
    
    return {"status": "sent", "user_id": user_id}


@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """Broadcast сообщение всем подключённым пользователям"""
    await manager.broadcast({
        "type": "broadcast",
        **message
    })
    
    return {"status": "broadcasted", "recipients": manager.get_connection_count()}


# === Эндпоинты для водителей ===

@router.post("/ws/driver/{user_id}/location")
async def update_driver_location(user_id: int, location: LocationUpdate):
    """
    Обновить локацию водителя через HTTP (альтернатива WebSocket).
    Используется если WebSocket недоступен.
    """
    state = driver_tracker.update_location_by_user(
        user_id=user_id,
        latitude=location.latitude,
        longitude=location.longitude,
        heading=location.heading,
        speed=location.speed,
        accuracy_m=location.accuracy_m
    )
    
    if not state:
        raise HTTPException(status_code=404, detail="Driver not registered in tracker")
    
    return {
        "status": "updated",
        "driver_status": state.status.value,
        "location": {
            "lat": state.latitude,
            "lng": state.longitude
        }
    }


@router.post("/ws/driver/{user_id}/status")
async def update_driver_status(user_id: int, status_update: DriverStatusUpdate):
    """Обновить статус водителя (online/offline/busy/paused)"""
    try:
        status = DriverStatus(status_update.status.lower())
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Allowed: {[s.value for s in DriverStatus]}"
        )
    
    state = driver_tracker.set_status_by_user(user_id, status)
    
    if not state:
        raise HTTPException(status_code=404, detail="Driver not registered in tracker")
    
    return {
        "status": "updated",
        "driver_status": state.status.value
    }


@router.get("/ws/driver/{user_id}/state")
async def get_driver_state(user_id: int):
    """Получить текущее состояние водителя"""
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
            "speed": state.speed
        } if state.latitude else None,
        "current_ride_id": state.current_ride_id,
        "classes_allowed": list(state.classes_allowed),
        "rating": state.rating,
        "updated_at": state.updated_at.isoformat()
    }


@router.get("/ws/drivers/stats")
async def get_drivers_stats():
    """Статистика по водителям в трекере"""
    return {
        **driver_tracker.get_stats(),
        "ws_connections": manager.get_connection_count()
    }


# Создание роутера для экспорта
websocket_router = router
