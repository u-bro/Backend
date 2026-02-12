from enum import Enum


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
    DOCUMENT = "document"
    AVATAR = "document"


class RoleCode:
    USER = "user"
    DRIVER = "driver"
    ADMIN = "admin"