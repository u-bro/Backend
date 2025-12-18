"""
Matching Engine

Движок для подбора водителей к заказам.
Фильтрация по допускам, расстоянию, сортировка по релевантности.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

from app.services.driver_tracker import (
    driver_tracker, 
    DriverState, 
    DriverStatus,
    RideClass
)

logger = logging.getLogger(__name__)


@dataclass
class RideRequest:
    """Запрос на поездку для матчинга"""
    ride_id: int
    client_id: int
    ride_class: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    expected_fare: Optional[float] = None
    scheduled_at: Optional[datetime] = None
    max_wait_minutes: int = 5
    search_radius_km: float = 5.0


@dataclass
class DriverMatch:
    """Результат матчинга - подходящий водитель"""
    driver_profile_id: int
    user_id: int
    distance_km: float
    eta_minutes: float  # Примерное время прибытия
    rating: float
    score: float  # Итоговый скор для сортировки
    
    def to_dict(self) -> dict:
        return {
            "driver_profile_id": self.driver_profile_id,
            "user_id": self.user_id,
            "distance_km": round(self.distance_km, 2),
            "eta_minutes": round(self.eta_minutes, 1),
            "rating": round(self.rating, 2),
            "score": round(self.score, 3)
        }


class MatchingEngine:
    """
    Движок матчинга заказов и водителей.
    
    Алгоритм:
    1. Фильтрация по онлайн-статусу
    2. Фильтрация по допускам (класс поездки)
    3. Фильтрация по радиусу от точки подачи
    4. Расчёт скора (расстояние + рейтинг + время обновления)
    5. Сортировка и выдача топ-N
    """
    
    # Средняя скорость в городе для расчёта ETA
    AVG_CITY_SPEED_KMH = 30
    
    # Веса для расчёта скора
    WEIGHT_DISTANCE = 0.5    # Чем ближе, тем лучше
    WEIGHT_RATING = 0.3      # Чем выше рейтинг, тем лучше
    WEIGHT_FRESHNESS = 0.2   # Чем свежее локация, тем лучше
    
    # Максимум водителей для выдачи
    DEFAULT_LIMIT = 20
    
    def __init__(self):
        self.tracker = driver_tracker
    
    def find_drivers(
        self,
        ride_request: RideRequest,
        limit: int = DEFAULT_LIMIT
    ) -> List[DriverMatch]:
        """
        Найти подходящих водителей для заказа.
        
        Args:
            ride_request: Параметры заказа
            limit: Максимум водителей
        
        Returns:
            Список подходящих водителей, отсортированных по релевантности
        """
        # Получаем доступных водителей с нужным допуском
        available = self.tracker.get_available_drivers(
            ride_class=ride_request.ride_class,
            center_lat=ride_request.pickup_lat,
            center_lng=ride_request.pickup_lng,
            radius_km=ride_request.search_radius_km,
            limit=limit * 2  # Берём с запасом для фильтрации
        )
        
        if not available:
            logger.info(f"No available drivers for ride {ride_request.ride_id}")
            return []
        
        matches = []
        now = datetime.utcnow()
        
        for driver in available:
            # Расчёт расстояния
            distance = self.tracker._haversine_distance(
                ride_request.pickup_lat,
                ride_request.pickup_lng,
                driver.latitude,
                driver.longitude
            )
            
            # Расчёт ETA
            eta_minutes = (distance / self.AVG_CITY_SPEED_KMH) * 60
            
            # Расчёт скора
            score = self._calculate_score(driver, distance, now)
            
            matches.append(DriverMatch(
                driver_profile_id=driver.driver_profile_id,
                user_id=driver.user_id,
                distance_km=distance,
                eta_minutes=eta_minutes,
                rating=driver.rating,
                score=score
            ))
        
        # Сортировка по скору (больше = лучше)
        matches.sort(key=lambda m: -m.score)
        
        result = matches[:limit]
        logger.info(
            f"Found {len(result)} drivers for ride {ride_request.ride_id} "
            f"(class={ride_request.ride_class}, radius={ride_request.search_radius_km}km)"
        )
        
        return result
    
    def find_single_best(self, ride_request: RideRequest) -> Optional[DriverMatch]:
        """Найти лучшего водителя"""
        matches = self.find_drivers(ride_request, limit=1)
        return matches[0] if matches else None
    
    def expand_search(
        self,
        ride_request: RideRequest,
        max_radius_km: float = 15.0,
        step_km: float = 2.5
    ) -> List[DriverMatch]:
        """
        Расширяющийся поиск - увеличиваем радиус пока не найдём водителей.
        
        Args:
            ride_request: Параметры заказа
            max_radius_km: Максимальный радиус поиска
            step_km: Шаг увеличения радиуса
        
        Returns:
            Список найденных водителей
        """
        original_radius = ride_request.search_radius_km
        current_radius = original_radius
        
        while current_radius <= max_radius_km:
            ride_request.search_radius_km = current_radius
            matches = self.find_drivers(ride_request)
            
            if matches:
                ride_request.search_radius_km = original_radius
                return matches
            
            current_radius += step_km
            logger.info(f"Expanding search radius to {current_radius}km for ride {ride_request.ride_id}")
        
        ride_request.search_radius_km = original_radius
        return []
    
    def get_driver_feed(
        self,
        driver_profile_id: int,
        rides: List[dict],
        limit: int = 20
    ) -> List[dict]:
        """
        Получить ленту заказов для водителя.
        Фильтрует заказы по допускам водителя и расстоянию.
        
        Args:
            driver_profile_id: ID профиля водителя
            rides: Список доступных заказов
            limit: Максимум заказов
        
        Returns:
            Отфильтрованные и отсортированные заказы
        """
        driver = self.tracker.get_driver(driver_profile_id)
        if not driver or driver.latitude is None:
            return []
        
        relevant_rides = []
        
        for ride in rides:
            # Проверяем допуск
            ride_class = ride.get('ride_class', ride.get('class', 'economy'))
            if not driver.has_permit(ride_class):
                continue
            
            # Расчёт расстояния до точки подачи
            pickup_lat = ride.get('pickup_lat')
            pickup_lng = ride.get('pickup_lng')
            
            if pickup_lat is None or pickup_lng is None:
                continue
            
            distance = self.tracker._haversine_distance(
                driver.latitude, driver.longitude,
                float(pickup_lat), float(pickup_lng)
            )
            
            # Добавляем расстояние и ETA
            ride_with_distance = {
                **ride,
                'distance_to_pickup_km': round(distance, 2),
                'eta_minutes': round((distance / self.AVG_CITY_SPEED_KMH) * 60, 1)
            }
            relevant_rides.append((distance, ride_with_distance))
        
        # Сортируем по расстоянию
        relevant_rides.sort(key=lambda x: x[0])
        
        return [r[1] for r in relevant_rides[:limit]]
    
    def _calculate_score(
        self,
        driver: DriverState,
        distance_km: float,
        now: datetime
    ) -> float:
        """
        Расчёт скора водителя для сортировки.
        
        Формула: 
        score = w1*(1/distance) + w2*rating + w3*freshness
        
        Чем выше скор, тем лучше.
        """
        # Нормализованное расстояние (0-1, ближе = больше)
        distance_score = 1 / (1 + distance_km)
        
        # Нормализованный рейтинг (0-1)
        rating_score = driver.rating / 5.0
        
        # Свежесть локации (0-1, свежее = больше)
        age_seconds = (now - driver.updated_at).total_seconds()
        freshness_score = max(0, 1 - (age_seconds / 300))  # Затухание за 5 минут
        
        score = (
            self.WEIGHT_DISTANCE * distance_score +
            self.WEIGHT_RATING * rating_score +
            self.WEIGHT_FRESHNESS * freshness_score
        )
        
        return score
    
    def get_stats(self) -> dict:
        """Статистика матчинга"""
        return {
            "tracker_stats": self.tracker.get_stats(),
            "config": {
                "avg_speed_kmh": self.AVG_CITY_SPEED_KMH,
                "weights": {
                    "distance": self.WEIGHT_DISTANCE,
                    "rating": self.WEIGHT_RATING,
                    "freshness": self.WEIGHT_FRESHNESS
                }
            }
        }


# Глобальный экземпляр
matching_engine = MatchingEngine()
