from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.apps import apps
from django.contrib import admin
from django.db import DatabaseError
from django.db.models import Count, Q
from django.urls import NoReverseMatch, reverse
from django.utils import timezone


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntitySpec:
    app_label: str
    model_name: str
    label: str
    icon: str
    url_name: str
    dashboard: bool = False

    @property
    def key(self) -> str:
        return f"{self.app_label}.{self.model_name}"

    @property
    def model(self):
        return apps.get_model(self.app_label, self.model_name)


ENTITY_SPECS = (
    EntitySpec("admin_users", "User", "Пользователи", "fas fa-users", "admin:admin_users_user_changelist", True),
    EntitySpec("admin_drivers", "DriverProfile", "Водители", "fas fa-id-card", "admin:admin_drivers_driverprofile_changelist", True),
    EntitySpec("admin_drivers", "DriverModerationInfo", "Причины модерации", "fas fa-clipboard-list", "admin:admin_drivers_drivermoderationinfo_changelist"),
    EntitySpec("admin_drivers", "DriverProfileModeration", "Модерации профилей", "fas fa-user-check", "admin:admin_drivers_driverprofilemoderation_changelist"),
    EntitySpec("admin_rides", "Ride", "Поездки", "fas fa-route", "admin:admin_rides_ride_changelist", True),
    EntitySpec("admin_roles", "Role", "Роли", "fas fa-user-tag", "admin:admin_roles_role_changelist"),
    EntitySpec("admin_driver_documents", "DriverDocument", "Документы водителей", "fas fa-file-alt", "admin:admin_driver_documents_driverdocument_changelist", True),
    EntitySpec("admin_chat_messages", "ChatMessage", "Сообщения чатов", "fas fa-comments", "admin:admin_chat_messages_chatmessage_changelist"),
    EntitySpec("admin_commissions", "Commission", "Комиссии", "fas fa-percent", "admin:admin_commissions_commission_changelist"),
    EntitySpec("admin_commission_payments", "CommissionPayment", "Платежи комиссий", "fas fa-credit-card", "admin:admin_commission_payments_commissionpayment_changelist", True),
    EntitySpec("admin_ride_status_history", "RideStatusHistory", "История статусов", "fas fa-history", "admin:admin_ride_status_history_ridestatushistory_changelist"),
    EntitySpec("admin_cars", "Car", "Автомобили", "fas fa-car", "admin:admin_cars_car_changelist", True),
    EntitySpec("admin_car_photos", "CarPhoto", "Фото автомобилей", "fas fa-images", "admin:admin_car_photos_carphoto_changelist"),
    EntitySpec("admin_driver_locations", "DriverLocation", "Локации водителей", "fas fa-map-marker-alt", "admin:admin_driver_locations_driverlocation_changelist"),
    EntitySpec("admin_ride_drivers_requests", "RideDriversRequest", "Запросы водителей", "fas fa-directions", "admin:admin_ride_drivers_requests_ridedriversrequest_changelist"),
    EntitySpec("admin_push_notifications", "AdminPushNotification", "Push-уведомления", "fas fa-bell", "admin:admin_push_notifications_adminpushnotification_changelist", True),
    EntitySpec("admin_support", "SupportConversation", "Обращения поддержки", "fas fa-headset", "support-workspace", True),
)

ENTITY_SPECS_BY_KEY = {spec.key.lower(): spec for spec in ENTITY_SPECS}


def get_entity_spec(app_label: str, model_name: str) -> EntitySpec | None:
    return ENTITY_SPECS_BY_KEY.get(f"{app_label}.{model_name}".lower())


def entity_stats(spec: EntitySpec, *, now=None) -> dict:
    now = now or timezone.now()
    cutoff = now - timedelta(hours=24)
    try:
        values = spec.model._default_manager.aggregate(
            total=Count("pk"),
            new_24h=Count("pk", filter=Q(created_at__gte=cutoff)),
        )
    except DatabaseError:
        logger.exception("Failed to load admin entity stats for %s", spec.key)
        return {
            "key": spec.key,
            "label": spec.label,
            "total": None,
            "new_24h": None,
            "updated_at": now.isoformat(),
            "available": False,
        }

    return {
        "key": spec.key,
        "label": spec.label,
        "total": values["total"],
        "new_24h": values["new_24h"],
        "updated_at": now.isoformat(),
        "available": True,
    }


def entity_url(spec: EntitySpec, request=None) -> str | None:
    if request is not None and spec.app_label != "admin_support":
        model_admin = admin.site._registry.get(spec.model)
        if model_admin is not None and not model_admin.has_view_permission(request):
            return None
    elif request is not None and spec.app_label == "admin_support":
        from admin_support.views import can_access_support

        if not can_access_support(request.user):
            return None

    try:
        return reverse(spec.url_name)
    except NoReverseMatch:
        logger.exception("Failed to reverse admin URL %s", spec.url_name)
        return None


def dashboard_entity_cards(request=None, *, now=None) -> list[dict]:
    cards = []
    for spec in ENTITY_SPECS:
        if not spec.dashboard:
            continue
        card = entity_stats(spec, now=now)
        card.update({"icon": spec.icon, "url": entity_url(spec, request)})
        cards.append(card)
    return cards


def grouped_counts(model, field: str, *, filters=None, labels=None) -> dict[str, int]:
    queryset = model._default_manager.all()
    if filters:
        queryset = queryset.filter(**filters)
    try:
        choices = dict(model._meta.get_field(field).flatchoices)
        rows = {
            row[field]: row["count"]
            for row in queryset.values(field).annotate(count=Count("pk")).order_by()
        }
        known_values = dict.fromkeys((*choices, *(labels or {}), *rows))
        result = {}
        for value in known_values:
            label = str((labels or {}).get(value, choices.get(value, value or "Не указан")))
            result[label] = result.get(label, 0) + rows.get(value, 0)
        return result
    except DatabaseError:
        logger.exception("Failed to load grouped admin stats for %s.%s", model._meta.label, field)
        return {}


def safe_count(queryset) -> int | None:
    try:
        return queryset.count()
    except DatabaseError:
        logger.exception("Failed to count admin queryset for %s", queryset.model._meta.label)
        return None
