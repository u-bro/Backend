from importlib import import_module
from typing import Any


_EXPORTS = {
    "ConnectionManager": ("app.services.websocket_manager", "ConnectionManager"),
    "manager": ("app.services.websocket_manager", "manager"),
    "manager_driver_feed": ("app.services.websocket_manager", "manager_driver_feed"),
    "manager_notifications": ("app.services.websocket_manager", "manager_notifications"),
    "fcm_service": ("app.services.fcm_service", "fcm_service"),
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
