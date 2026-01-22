from dataclasses import dataclass, field
from typing import Optional, Set
from app.enum import DriverStatus
from datetime import datetime, timezone


@dataclass
class DriverState:
    driver_profile_id: int
    user_id: int
    status: DriverStatus = DriverStatus.OFFLINE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    classes_allowed: Set[str] = field(default_factory=set)
    current_ride_id: Optional[int] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_available(self) -> bool:
        return (
            self.status == DriverStatus.ONLINE
            and self.current_ride_id is None
            and self.latitude is not None
        )

    def has_permit(self, ride_class: str) -> bool:
        return ride_class.lower() in {c.lower() for c in self.classes_allowed}