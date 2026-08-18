from urllib.parse import urlencode, urlsplit

from django.urls import reverse
from django.utils.html import format_html


EMPTY_VALUE = "—"


def safe_external_url(value):
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def admin_change_link(value, app_label, model_name, label=None):
    if value is None:
        return EMPTY_VALUE

    url = reverse(f"admin:{app_label}_{model_name}_change", args=[value])
    return format_html('<a href="{}">{}</a>', url, label if label is not None else value)


def user_link(value, label=None):
    return admin_change_link(value, "admin_users", "user", label)


def ride_link(value, label=None):
    return admin_change_link(value, "admin_rides", "ride", label)


def car_link(value, label=None):
    return admin_change_link(value, "admin_cars", "car", label)


def driver_profile_link(value, label=None, source="profiles"):
    if value is None:
        return EMPTY_VALUE

    url = reverse("driver-moderation-detail", args=[value])
    if source:
        url = f"{url}?{urlencode({'from': source})}"
    return format_html('<a href="{}">{}</a>', url, label if label is not None else value)
