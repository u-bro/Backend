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
    AVATAR = S3_DOCUMENTS_BUCKET


class RoleCode:
    USER = "user"
    DRIVER = "driver"
    ADMIN = "admin"