"""
Order Dispatcher Service

Сервис для рассылки новых заказов релевантным водителям.
При создании заказа находит подходящих водителей и отправляет им push через WebSocket.
"""

from typing import Optional, List
from datetime import datetime
import asyncio
import logging

from app.services.driver_tracker import driver_tracker
from app.services.matching_engine import matching_engine, RideRequest, DriverMatch
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)


class OrderDispatcher:
    """
    Диспетчер заказов.
    
    Отвечает за:
    1. Рассылку новых заказов подходящим водителям
    2. Отслеживание откликов
    3. Повторную рассылку при отсутствии отклика
    """
    
    # Настройки рассылки
    DEFAULT_RADIUS_KM = 3.0
    MAX_RADIUS_KM = 15.0
    RADIUS_STEP_KM = 2.0
    MAX_DRIVERS_PER_WAVE = 10
    WAVE_INTERVAL_SECONDS = 15
    MAX_WAVES = 5
    
    def __init__(self):
        # ride_id -> {notified_drivers: set, created_at: datetime, waves: int}
        self._active_dispatches: dict[int, dict] = {}
    
    async def dispatch_new_ride(
        self,
        ride_id: int,
        client_id: int,
        ride_class: str,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: Optional[float] = None,
        dropoff_lng: Optional[float] = None,
        expected_fare: Optional[float] = None,
        pickup_address: Optional[str] = None,
        dropoff_address: Optional[str] = None,
    ) -> dict:
        """
        Разослать новый заказ релевантным водителям.
        
        Args:
            ride_id: ID заказа
            client_id: ID клиента
            ride_class: Класс поездки (economy, comfort, etc.)
            pickup_lat, pickup_lng: Координаты подачи
            dropoff_lat, dropoff_lng: Координаты назначения (опционально)
            expected_fare: Ожидаемая стоимость
            pickup_address, dropoff_address: Адреса
        
        Returns:
            Статистика рассылки
        """
        # Создаём запрос на поиск
        request = RideRequest(
            ride_id=ride_id,
            client_id=client_id,
            ride_class=ride_class,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            expected_fare=expected_fare,
            search_radius_km=self.DEFAULT_RADIUS_KM
        )
        
        # Ищем водителей с расширением радиуса
        drivers = matching_engine.expand_search(
            request,
            max_radius_km=self.MAX_RADIUS_KM,
            step_km=self.RADIUS_STEP_KM
        )
        
        if not drivers:
            logger.warning(f"No available drivers for ride {ride_id}")
            return {
                "ride_id": ride_id,
                "notified_count": 0,
                "message": "No available drivers found"
            }
        
        # Берём первую волну водителей
        first_wave = drivers[:self.MAX_DRIVERS_PER_WAVE]
        
        # Формируем сообщение для push
        ride_data = {
            "type": "new_ride",
            "ride_id": ride_id,
            "ride_class": ride_class,
            "pickup": {
                "address": pickup_address,
                "lat": pickup_lat,
                "lng": pickup_lng
            },
            "dropoff": {
                "address": dropoff_address,
                "lat": dropoff_lat,
                "lng": dropoff_lng
            } if dropoff_lat else None,
            "expected_fare": expected_fare,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Рассылаем
        notified = []
        for driver in first_wave:
            # Добавляем персональные данные для этого водителя
            personal_data = {
                **ride_data,
                "your_distance_km": driver.distance_km,
                "your_eta_minutes": driver.eta_minutes
            }
            
            success = await manager.send_personal_message(
                driver.user_id,
                personal_data
            )
            
            if success:
                notified.append({
                    "driver_profile_id": driver.driver_profile_id,
                    "user_id": driver.user_id,
                    "distance_km": driver.distance_km
                })
        
        # Сохраняем информацию о рассылке
        self._active_dispatches[ride_id] = {
            "notified_drivers": {d["driver_profile_id"] for d in notified},
            "all_candidates": [d.driver_profile_id for d in drivers],
            "created_at": datetime.utcnow(),
            "waves": 1
        }
        
        logger.info(
            f"Dispatched ride {ride_id} to {len(notified)} drivers "
            f"(class={ride_class}, total_candidates={len(drivers)})"
        )
        
        return {
            "ride_id": ride_id,
            "ride_class": ride_class,
            "notified_count": len(notified),
            "total_candidates": len(drivers),
            "notified_drivers": notified
        }
    
    async def dispatch_next_wave(self, ride_id: int) -> dict:
        """
        Отправить следующую волну водителям.
        Вызывается если первая волна не откликнулась.
        """
        dispatch = self._active_dispatches.get(ride_id)
        if not dispatch:
            return {"error": "Dispatch not found", "ride_id": ride_id}
        
        if dispatch["waves"] >= self.MAX_WAVES:
            return {
                "ride_id": ride_id,
                "message": "Max waves reached",
                "waves": dispatch["waves"]
            }
        
        # Находим водителей, которых ещё не оповещали
        already_notified = dispatch["notified_drivers"]
        all_candidates = dispatch["all_candidates"]
        
        remaining = [
            dpid for dpid in all_candidates 
            if dpid not in already_notified
        ]
        
        if not remaining:
            return {
                "ride_id": ride_id,
                "message": "No more drivers to notify",
                "waves": dispatch["waves"]
            }
        
        # Берём следующую порцию
        next_batch = remaining[:self.MAX_DRIVERS_PER_WAVE]
        
        # TODO: Получить ride_data из БД или кэша
        # Пока упрощённое уведомление
        notified = []
        for dpid in next_batch:
            driver = driver_tracker.get_driver(dpid)
            if driver and manager.is_connected(driver.user_id):
                await manager.send_personal_message(driver.user_id, {
                    "type": "new_ride_reminder",
                    "ride_id": ride_id,
                    "message": "Заказ всё ещё доступен!",
                    "wave": dispatch["waves"] + 1
                })
                notified.append(dpid)
                dispatch["notified_drivers"].add(dpid)
        
        dispatch["waves"] += 1
        
        return {
            "ride_id": ride_id,
            "wave": dispatch["waves"],
            "notified_count": len(notified)
        }
    
    async def cancel_dispatch(self, ride_id: int) -> bool:
        """Отменить рассылку (заказ принят или отменён)"""
        if ride_id in self._active_dispatches:
            dispatch = self._active_dispatches.pop(ride_id)
            
            # Уведомляем всех оповещённых водителей
            for dpid in dispatch["notified_drivers"]:
                driver = driver_tracker.get_driver(dpid)
                if driver:
                    await manager.send_personal_message(driver.user_id, {
                        "type": "ride_unavailable",
                        "ride_id": ride_id,
                        "message": "Заказ больше недоступен"
                    })
            
            logger.info(f"Canceled dispatch for ride {ride_id}")
            return True
        
        return False
    
    def get_dispatch_status(self, ride_id: int) -> Optional[dict]:
        """Получить статус рассылки"""
        dispatch = self._active_dispatches.get(ride_id)
        if not dispatch:
            return None
        
        return {
            "ride_id": ride_id,
            "notified_count": len(dispatch["notified_drivers"]),
            "total_candidates": len(dispatch["all_candidates"]),
            "waves": dispatch["waves"],
            "age_seconds": (datetime.utcnow() - dispatch["created_at"]).total_seconds()
        }
    
    def get_active_dispatches(self) -> List[int]:
        """Список активных рассылок"""
        return list(self._active_dispatches.keys())
    
    def cleanup_old_dispatches(self, max_age_seconds: int = 600) -> int:
        """Удалить старые рассылки (по умолчанию старше 10 минут)"""
        threshold = datetime.utcnow()
        to_remove = []
        
        for ride_id, dispatch in self._active_dispatches.items():
            age = (threshold - dispatch["created_at"]).total_seconds()
            if age > max_age_seconds:
                to_remove.append(ride_id)
        
        for ride_id in to_remove:
            del self._active_dispatches[ride_id]
            logger.info(f"Cleaned up stale dispatch for ride {ride_id}")
        
        return len(to_remove)


# Глобальный экземпляр
order_dispatcher = OrderDispatcher()
