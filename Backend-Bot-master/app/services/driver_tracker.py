"""
Driver Tracker Service

Сервис для отслеживания геолокации и статуса водителей в реальном времени.
Хранит данные в памяти для быстрого доступа (можно заменить на Redis в продакшене).
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import math
import logging

logger = logging.getLogger(__name__)


class DriverStatus(str, Enum):
    """Статус водителя"""
    OFFLINE = "offline"      # Не в сети
    ONLINE = "online"        # Готов принимать заказы
    BUSY = "busy"            # На заказе
    PAUSED = "paused"        # Временно не принимает заказы


class RideClass(str, Enum):
    """Классы поездок (допуски)"""
    ECONOMY = "economy"          # Эконом
    COMFORT = "comfort"          # Комфорт
    COMFORT_PLUS = "comfort_plus"  # Комфорт+
    BUSINESS = "business"        # Бизнес
    PREMIUM = "premium"          # Премиум
    CARGO = "cargo"              # Грузовой
    DELIVERY = "delivery"        # Доставка
    MINIVAN = "minivan"          # Минивэн


@dataclass
class DriverState:
    """Состояние водителя в памяти"""
    driver_profile_id: int
    user_id: int
    status: DriverStatus = DriverStatus.OFFLINE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading: Optional[float] = None  # Направление движения (градусы)
    speed: Optional[float] = None    # Скорость км/ч
    accuracy_m: Optional[int] = None
    classes_allowed: Set[str] = field(default_factory=set)
    current_ride_id: Optional[int] = None
    rating: float = 5.0
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_available(self) -> bool:
        """Доступен ли для новых заказов"""
        return (
            self.status == DriverStatus.ONLINE 
            and self.current_ride_id is None
            and self.latitude is not None
        )
    
    def has_permit(self, ride_class: str) -> bool:
        """Есть ли допуск к классу поездки"""
        return ride_class.lower() in {c.lower() for c in self.classes_allowed}


class DriverTracker:
    """
    Менеджер отслеживания водителей.
    
    Хранит состояние всех водителей в памяти для быстрого матчинга.
    В продакшене можно заменить на Redis для масштабирования.
    """
    
    # Timeout для автоматического перевода в offline
    OFFLINE_TIMEOUT_SECONDS = 120  # 2 минуты без обновлений -> offline
    
    def __init__(self):
        # driver_profile_id -> DriverState
        self._drivers: Dict[int, DriverState] = {}
        # user_id -> driver_profile_id (для быстрого поиска)
        self._user_to_driver: Dict[int, int] = {}
        # ride_class -> Set[driver_profile_id] (индекс по допускам)
        self._class_index: Dict[str, Set[int]] = {}
    
    def register_driver(
        self,
        driver_profile_id: int,
        user_id: int,
        classes_allowed: List[str],
        rating: float = 5.0
    ) -> DriverState:
        """Регистрация/обновление водителя в системе"""
        classes_set = {c.lower() for c in classes_allowed}
        
        if driver_profile_id in self._drivers:
            state = self._drivers[driver_profile_id]
            state.classes_allowed = classes_set
            state.rating = rating
        else:
            state = DriverState(
                driver_profile_id=driver_profile_id,
                user_id=user_id,
                classes_allowed=classes_set,
                rating=rating
            )
            self._drivers[driver_profile_id] = state
            self._user_to_driver[user_id] = driver_profile_id
        
        # Обновляем индекс по допускам
        self._update_class_index(driver_profile_id, classes_set)
        
        logger.info(f"Driver {driver_profile_id} registered with classes: {classes_set}")
        return state
    
    def update_location(
        self,
        driver_profile_id: int,
        latitude: float,
        longitude: float,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
        accuracy_m: Optional[int] = None
    ) -> Optional[DriverState]:
        """Обновление геолокации водителя"""
        if driver_profile_id not in self._drivers:
            logger.warning(f"Driver {driver_profile_id} not registered")
            return None
        
        state = self._drivers[driver_profile_id]
        state.latitude = latitude
        state.longitude = longitude
        state.heading = heading
        state.speed = speed
        state.accuracy_m = accuracy_m
        state.updated_at = datetime.utcnow()
        
        return state
    
    def update_location_by_user(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        **kwargs
    ) -> Optional[DriverState]:
        """Обновление локации по user_id (для WebSocket)"""
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            return self.update_location(driver_id, latitude, longitude, **kwargs)
        return None
    
    def set_status(
        self,
        driver_profile_id: int,
        status: DriverStatus
    ) -> Optional[DriverState]:
        """Изменение статуса водителя"""
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_status = state.status
        state.status = status
        state.updated_at = datetime.utcnow()
        
        logger.info(f"Driver {driver_profile_id} status: {old_status} -> {status}")
        return state
    
    def set_status_by_user(self, user_id: int, status: DriverStatus) -> Optional[DriverState]:
        """Изменение статуса по user_id"""
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            return self.set_status(driver_id, status)
        return None
    
    def assign_ride(self, driver_profile_id: int, ride_id: int) -> Optional[DriverState]:
        """Назначить поездку водителю"""
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        state.current_ride_id = ride_id
        state.status = DriverStatus.BUSY
        state.updated_at = datetime.utcnow()
        
        logger.info(f"Driver {driver_profile_id} assigned to ride {ride_id}")
        return state
    
    def release_ride(self, driver_profile_id: int) -> Optional[DriverState]:
        """Освободить водителя от поездки"""
        if driver_profile_id not in self._drivers:
            return None
        
        state = self._drivers[driver_profile_id]
        old_ride = state.current_ride_id
        state.current_ride_id = None
        state.status = DriverStatus.ONLINE
        state.updated_at = datetime.utcnow()
        
        logger.info(f"Driver {driver_profile_id} released from ride {old_ride}")
        return state
    
    def get_driver(self, driver_profile_id: int) -> Optional[DriverState]:
        """Получить состояние водителя"""
        return self._drivers.get(driver_profile_id)
    
    def get_driver_by_user(self, user_id: int) -> Optional[DriverState]:
        """Получить состояние по user_id"""
        driver_id = self._user_to_driver.get(user_id)
        if driver_id:
            return self._drivers.get(driver_id)
        return None
    
    def get_available_drivers(
        self,
        ride_class: Optional[str] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        radius_km: float = 10.0,
        limit: int = 50
    ) -> List[DriverState]:
        """
        Получить доступных водителей с фильтрацией.
        
        Args:
            ride_class: Фильтр по классу поездки
            center_lat: Центр поиска (широта)
            center_lng: Центр поиска (долгота)
            radius_km: Радиус поиска в км
            limit: Максимум водителей
        
        Returns:
            Список доступных водителей, отсортированных по расстоянию
        """
        candidates = []
        
        # Если указан класс, берём из индекса
        if ride_class:
            driver_ids = self._class_index.get(ride_class.lower(), set())
            drivers = [self._drivers[did] for did in driver_ids if did in self._drivers]
        else:
            drivers = list(self._drivers.values())
        
        for driver in drivers:
            if not driver.is_available():
                continue
            
            if ride_class and not driver.has_permit(ride_class):
                continue
            
            # Расчёт расстояния если указан центр
            distance = None
            if center_lat is not None and center_lng is not None:
                if driver.latitude is None or driver.longitude is None:
                    continue
                
                distance = self._haversine_distance(
                    center_lat, center_lng,
                    driver.latitude, driver.longitude
                )
                
                if distance > radius_km:
                    continue
            
            candidates.append((driver, distance))
        
        # Сортировка: по расстоянию (если есть), затем по рейтингу
        candidates.sort(key=lambda x: (x[1] if x[1] else 0, -x[0].rating))
        
        return [c[0] for c in candidates[:limit]]
    
    def get_online_count(self) -> int:
        """Количество водителей онлайн"""
        return sum(1 for d in self._drivers.values() if d.status == DriverStatus.ONLINE)
    
    def get_busy_count(self) -> int:
        """Количество водителей на заказах"""
        return sum(1 for d in self._drivers.values() if d.status == DriverStatus.BUSY)
    
    def get_stats(self) -> dict:
        """Статистика по водителям"""
        return {
            "total_registered": len(self._drivers),
            "online": self.get_online_count(),
            "busy": self.get_busy_count(),
            "offline": sum(1 for d in self._drivers.values() if d.status == DriverStatus.OFFLINE),
        }
    
    def cleanup_stale(self) -> int:
        """Перевести в offline водителей без обновлений"""
        threshold = datetime.utcnow() - timedelta(seconds=self.OFFLINE_TIMEOUT_SECONDS)
        count = 0
        
        for driver in self._drivers.values():
            if driver.status != DriverStatus.OFFLINE and driver.updated_at < threshold:
                driver.status = DriverStatus.OFFLINE
                count += 1
                logger.info(f"Driver {driver.driver_profile_id} auto-offline (stale)")
        
        return count
    
    def _update_class_index(self, driver_id: int, classes: Set[str]):
        """Обновить индекс допусков"""
        # Удалить из старых классов
        for class_drivers in self._class_index.values():
            class_drivers.discard(driver_id)
        
        # Добавить в новые
        for cls in classes:
            if cls not in self._class_index:
                self._class_index[cls] = set()
            self._class_index[cls].add(driver_id)
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Расстояние между двумя точками в километрах (формула гаверсинусов)"""
        R = 6371  # Радиус Земли в км
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# Глобальный экземпляр трекера
driver_tracker = DriverTracker()
