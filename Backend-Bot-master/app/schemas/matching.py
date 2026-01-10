from typing import Optional, Literal
from .base import BaseSchema


class LocationUpdate(BaseSchema):
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy_m: Optional[int] = None
