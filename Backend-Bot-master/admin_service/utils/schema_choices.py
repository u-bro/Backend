from utils.moderation_labels import DOCUMENT_LABELS, STATUS_LABELS

RIDE_CLASS_VALUES = ("light", "pro", "vip", "elite")
RIDE_CLASS_CHOICES = (
    ("light", "Лайт"),
    ("pro", "Про"),
    ("vip", "ВИП"),
    ("elite", "Элит"),
)

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
RIDE_STATUS_CHOICES = (
    ("requested", "Ожидает отклика"),
    ("canceled", "Отменена"),
    ("waiting_commission", "Ожидает оплаты комиссии"),
    ("accepted", "Принята"),
    ("on_the_way", "Водитель в пути"),
    ("arrived", "Водитель прибыл"),
    ("started", "Выполняется"),
    ("completed", "Завершена"),
)

RIDE_TYPE_VALUES = ("with_car", "without_car", "delivery")
RIDE_TYPE_CHOICES = (
    ("with_car", "С автомобилем"),
    ("without_car", "Без автомобиля"),
    ("delivery", "Доставка"),
)

USER_STATUS_VALUES = ("waiting_register", "active")
USER_STATUS_CHOICES = (
    ("waiting_register", "Регистрация не завершена"),
    ("active", "Активен"),
)

DRIVER_PROFILE_STATUS_VALUES = (
    "waiting_register",
    "waiting_approved",
    "waiting_moderation",
    "rejected",
    "approved",
)
DRIVER_PROFILE_STATUS_CHOICES = (
    ("waiting_register", "Регистрация не завершена"),
    ("waiting_approved", "Проверка данных"),
    ("waiting_moderation", "Модерация документов"),
    ("rejected", "Отклонённые заявки"),
    ("approved", "Принят"),
)

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
DRIVER_DOCUMENT_TYPE_CHOICES = tuple((value, DOCUMENT_LABELS[value]) for value in DRIVER_DOCUMENT_TYPE_VALUES)

DRIVER_DOCUMENT_STATUS_VALUES = ("created", "updated", "approved", "rejected")
DRIVER_DOCUMENT_STATUS_CHOICES = tuple((value, STATUS_LABELS[value]) for value in DRIVER_DOCUMENT_STATUS_VALUES)

CAR_PHOTO_STATUS_VALUES = ("created", "updated", "approved", "rejected")
CAR_PHOTO_STATUS_CHOICES = tuple((value, STATUS_LABELS[value]) for value in CAR_PHOTO_STATUS_VALUES)

RIDE_DRIVERS_REQUEST_STATUS_VALUES = ("requested", "accepted", "rejected", "canceled")
RIDE_DRIVERS_REQUEST_STATUS_CHOICES = (
    ("requested", "Ожидает отклика"),
    ("accepted", "Принята"),
    ("rejected", "Отклонена"),
    ("canceled", "Отменена"),
)
RIDE_REQUEST_REMOVAL_REASON_VALUES = (
    "selected_other_driver",
    "ride_canceled",
    "ride_expired",
    "driver_withdrawn",
    "driver_offline",
    "driver_profile_resubmitted",
    "driver_assigned_elsewhere",
)
RIDE_REQUEST_REMOVAL_REASON_CHOICES = (
    ("selected_other_driver", "Выбран другой водитель"),
    ("ride_canceled", "Поездка отменена"),
    ("ride_expired", "Время ожидания поездки истекло"),
    ("driver_withdrawn", "Водитель отозвал отклик"),
    ("driver_offline", "Водитель не в сети"),
    ("driver_profile_resubmitted", "Анкета отправлена на повторную проверку"),
    ("driver_assigned_elsewhere", "Водитель назначен на другую поездку"),
)

DRIVER_LOCATION_STATUS_VALUES = ("offline", "online", "busy", "waiting_ride")
DRIVER_LOCATION_STATUS_CHOICES = (
    ("offline", "Не в сети"),
    ("online", "В сети"),
    ("busy", "Занят"),
    ("waiting_ride", "Ожидает поездку"),
)

ROLE_CODE_VALUES = ("user", "driver", "admin")
ROLE_CODE_CHOICES = (
    ("user", "Пользователь"),
    ("driver", "Водитель"),
    ("admin", "Администратор"),
)
