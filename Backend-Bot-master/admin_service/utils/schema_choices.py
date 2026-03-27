RIDE_CLASS_VALUES = ("light", "pro", "vip", "elite")
RIDE_CLASS_CHOICES = tuple((value, value) for value in RIDE_CLASS_VALUES)

RIDE_STATUS_VALUES = (
    "requested",
    "canceled",
    "waiting_commission",
    "accepted",
    "on_the_way",
    "arrived",
    "started",
    "completed",
)
RIDE_STATUS_CHOICES = tuple((value, value) for value in RIDE_STATUS_VALUES)

RIDE_TYPE_VALUES = ("with_car", "without_car", "delivery")
RIDE_TYPE_CHOICES = tuple((value, value) for value in RIDE_TYPE_VALUES)

USER_STATUS_VALUES = ("waiting_register", "active")
USER_STATUS_CHOICES = tuple((value, value) for value in USER_STATUS_VALUES)

DRIVER_PROFILE_STATUS_VALUES = (
    "waiting_register",
    "waiting_approved",
    "waiting_moderation",
    "approved",
)
DRIVER_PROFILE_STATUS_CHOICES = tuple((value, value) for value in DRIVER_PROFILE_STATUS_VALUES)

DRIVER_DOCUMENT_TYPE_VALUES = (
    "PASSPORT_FRONT",
    "PASSPORT_REGISTRATION",
    "DRIVER_LICENSE_FRONT",
    "DRIVER_LICENSE_BACK",
    "STS_FRONT",
    "STS_BACK",
    "CAR_PHOTO_FRONT",
    "CAR_PHOTO_LEFT",
    "CAR_PHOTO_REAR",
    "CAR_PHOTO_RIGHT",
    "CAR_PHOTO_FRONT_SEATS",
    "CAR_PHOTO_REAR_SEATS",
    "CAR_PHOTO_TRUNK",
)
DRIVER_DOCUMENT_TYPE_CHOICES = tuple((value, value) for value in DRIVER_DOCUMENT_TYPE_VALUES)

DRIVER_DOCUMENT_STATUS_VALUES = ("created", "updated", "approved", "rejected")
DRIVER_DOCUMENT_STATUS_CHOICES = tuple((value, value) for value in DRIVER_DOCUMENT_STATUS_VALUES)

CAR_PHOTO_STATUS_VALUES = ("created", "updated", "approved", "rejected")
CAR_PHOTO_STATUS_CHOICES = tuple((value, value) for value in CAR_PHOTO_STATUS_VALUES)

RIDE_DRIVERS_REQUEST_STATUS_VALUES = ("requested", "accepted", "rejected", "canceled")
RIDE_DRIVERS_REQUEST_STATUS_CHOICES = tuple((value, value) for value in RIDE_DRIVERS_REQUEST_STATUS_VALUES)

DRIVER_LOCATION_STATUS_VALUES = ("offline", "online", "busy", "waiting_ride")
DRIVER_LOCATION_STATUS_CHOICES = tuple((value, value) for value in DRIVER_LOCATION_STATUS_VALUES)

ROLE_CODE_VALUES = ("user", "driver", "admin")
ROLE_CODE_CHOICES = tuple((value, value) for value in ROLE_CODE_VALUES)
