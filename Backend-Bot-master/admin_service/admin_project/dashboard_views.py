from __future__ import annotations

from django.contrib import admin
from django.db import DatabaseError
from django.db.models import BigIntegerField, F, Value
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from admin_commission_payments.models import CommissionPayment
from admin_drivers.models import DriverProfile
from admin_push_notifications.models import AdminPushNotification
from admin_rides.models import Ride
from admin_support.models import SupportConversation, SupportMessage
from admin_users.models import User
from utils.admin_stats import (
    dashboard_entity_cards,
    entity_stats,
    get_entity_spec,
    grouped_counts,
    safe_count,
)


DRIVER_QUEUE_STATUSES = (
    DriverProfile.STATUS_WAITING_APPROVED,
    DriverProfile.STATUS_WAITING_MODERATION,
)
FAILED_PAYMENT_STATUSES = (
    "AUTH_FAIL",
    "REJECTED",
    "DEADLINE_EXPIRED",
    "CANCELED",
    "CANCELLED",
)
PAYMENT_STATUS_LABELS = {
    "NEW": "Созданы",
    "FORM_SHOWED": "Форма открыта",
    "AUTHORIZING": "Авторизация",
    "AUTHORIZED": "Авторизованы",
    "CONFIRMING": "Подтверждаются",
    "CONFIRMED": "Оплачены",
    "REVERSING": "Отменяются",
    "REVERSED": "Отменены",
    "REFUNDING": "Возвращаются",
    "PARTIAL_REFUNDED": "Частично возвращены",
    "REFUNDED": "Возвращены",
    "AUTH_FAIL": "Ошибка авторизации",
    "REJECTED": "Отклонены",
    "DEADLINE_EXPIRED": "Истёк срок",
    "CANCELED": "Отменены",
    "CANCELLED": "Отменены",
}


def _unread_support_counts():
    read_marker = Coalesce(
        F("conversation__last_read_message_id"),
        Value(0),
        output_field=BigIntegerField(),
    )
    unread = SupportMessage.objects.filter(
        sender_type="USER",
        id__gt=read_marker,
    )
    return {
        "messages": safe_count(unread),
        "conversations": safe_count(unread.values("conversation_id").distinct()),
    }


def _recent(queryset):
    try:
        return list(queryset[:6])
    except DatabaseError:
        return []


def _can_view_model(request, model):
    model_admin = admin.site._registry.get(model)
    return bool(model_admin and model_admin.has_view_permission(request))


def _snapshot(request):
    cards = dashboard_entity_cards(request)
    unread = _unread_support_counts()
    attention = {
        "moderation_queue": safe_count(DriverProfile.objects.filter(status__in=DRIVER_QUEUE_STATUSES)),
        "open_support": safe_count(SupportConversation.objects.filter(status="OPEN")),
        "unread_support": unread["conversations"],
        "active_rides": safe_count(Ride.objects.exclude(status__in=("completed", "canceled"))),
        "failed_pushes": safe_count(AdminPushNotification.objects.filter(status__in=("failed", "partial"))),
        "problem_payments": safe_count(CommissionPayment.objects.filter(status__in=FAILED_PAYMENT_STATUSES)),
    }
    return {
        "updated_at": timezone.now().isoformat(),
        "cards": cards,
        "attention": attention,
        "statuses": {
            "drivers": grouped_counts(DriverProfile, "status"),
            "rides": grouped_counts(Ride, "status"),
            "support": grouped_counts(
                SupportConversation,
                "status",
                labels={"OPEN": "Открытые", "CLOSED": "Закрытые"},
            ),
            "pushes": grouped_counts(AdminPushNotification, "status"),
            "payments": grouped_counts(
                CommissionPayment,
                "status",
                labels=PAYMENT_STATUS_LABELS,
            ),
        },
    }


@require_GET
def dashboard_view(request):
    snapshot = _snapshot(request)
    from admin_support.views import can_access_support

    can_view_users = _can_view_model(request, User)
    can_view_drivers = _can_view_model(request, DriverProfile)
    can_view_rides = _can_view_model(request, Ride)
    can_view_support = can_access_support(request.user)
    context = {
        **admin.site.each_context(request),
        "title": "Операционный дашборд",
        "dashboard_stats_url": reverse("admin-dashboard-stats"),
        "dashboard": snapshot,
        "can_view_users": can_view_users,
        "can_view_drivers": can_view_drivers,
        "can_view_rides": can_view_rides,
        "can_view_support": can_view_support,
        "recent_users": _recent(User.objects.order_by("-created_at", "-id")) if can_view_users else [],
        "recent_drivers": _recent(DriverProfile.objects.order_by("-created_at", "-id")) if can_view_drivers else [],
        "recent_rides": _recent(Ride.objects.order_by("-created_at", "-id")) if can_view_rides else [],
        "recent_support": _recent(SupportConversation.objects.select_related("user").order_by("-created_at", "-id")) if can_view_support else [],
    }
    return render(request, "admin/dashboard.html", context)


@require_GET
def dashboard_stats(request):
    return JsonResponse(_snapshot(request))


@require_GET
def entity_stats_view(request, app_label: str, model_name: str):
    spec = get_entity_spec(app_label, model_name)
    if spec is None:
        raise Http404("Entity stats are not available")
    return JsonResponse(entity_stats(spec))
