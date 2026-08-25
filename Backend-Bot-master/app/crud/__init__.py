from importlib import import_module
from typing import Any


_EXPORTS = {
    "CrudBase": ("app.crud.base", "CrudBase"),
    "user_crud": ("app.crud.user", "user_crud"),
    "ride_crud": ("app.crud.ride", "ride_crud"),
    "role_crud": ("app.crud.role", "role_crud"),
    "driver_profile_crud": ("app.crud.driver_profile", "driver_profile_crud"),
    "driver_document_crud": ("app.crud.driver_document", "driver_document_crud"),
    "phone_verification_crud": ("app.crud.phone_verification", "phone_verification_crud"),
    "commission_crud": ("app.crud.commission", "commission_crud"),
    "document_crud": ("app.crud.document", "document_crud"),
    "driver_location_crud": ("app.crud.driver_location", "driver_location_crud"),
    "in_app_notification_crud": ("app.crud.in_app_notification", "in_app_notification_crud"),
    "device_token_crud": ("app.crud.device_token", "device_token_crud"),
    "commission_payment_crud": ("app.crud.commission_payment", "commission_payment_crud"),
    "ride_drivers_request_crud": ("app.crud.ride_drivers_request", "ride_drivers_request_crud"),
    "car_crud": ("app.crud.car", "car_crud"),
    "driver_feed": ("app.crud.driver_feed", "driver_feed"),
    "driver_tracker": ("app.crud.driver_tracker", "driver_tracker"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
