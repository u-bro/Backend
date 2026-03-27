from typing import Literal
from enum import Enum
from .config import S3_DOCUMENTS_BUCKET, S3_AVATARS_BUCKET


class DriverStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    WAITING_RIDE = "waiting_ride"
    NOT_CONNECTED = "not_connected"


class MessageType:
    TEXT = "text"
    IMAGE = "image"
    LOCATION = "location"
    SYSTEM = "system"  
    VOICE = "voice"


class S3Bucket:
    DOCUMENT = S3_DOCUMENTS_BUCKET
    AVATAR = S3_AVATARS_BUCKET


class RoleCode:
    USER = "user"
    DRIVER = "driver"
    ADMIN = "admin"

class RideClass:
    LIGHT = "light"
    PRO = "pro"
    VIP = "vip"
    ELITE = "elite"

class DriverDocumentType(Enum):
    PASSPORT_FRONT = "PASSPORT_FRONT"
    PASSPORT_REGISTRATION = "PASSPORT_REGISTRATION"
    DRIVER_LICENSE_FRONT = "DRIVER_LICENSE_FRONT"
    DRIVER_LICENSE_BACK = "DRIVER_LICENSE_BACK"
    STS_FRONT = "STS_FRONT"
    STS_BACK = "STS_BACK"
    CAR_PHOTO_FRONT = "CAR_PHOTO_FRONT"
    CAR_PHOTO_LEFT = "CAR_PHOTO_LEFT"
    CAR_PHOTO_REAR = "CAR_PHOTO_REAR"
    CAR_PHOTO_RIGHT = "CAR_PHOTO_RIGHT"
    CAR_PHOTO_FRONT_SEATS = "CAR_PHOTO_FRONT_SEATS"
    CAR_PHOTO_REAR_SEATS = "CAR_PHOTO_REAR_SEATS"
    CAR_PHOTO_TRUNK = "CAR_PHOTO_TRUNK"
