from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlencode

from django.contrib import messages
from django.db import connection, models, transaction
from django.db.models import Case, IntegerField, Q, Subquery, Value, When
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from admin_cars.models import Car
from admin_car_photos.models import CarPhoto
from admin_driver_documents.models import DriverDocument
from admin_driver_locations.models import DriverLocation
from admin_ride_drivers_requests.models import RideDriversRequest
from admin_rides.models import Ride
from admin_users.models import User
from utils.api_client import api_client

from .forms import DriverModerationForm
from .models import DriverModerationInfo, DriverProfile, DriverProfileModeration


STATUS_LABELS = {
    "waiting_register": "Ожидает регистрации",
    "waiting_approved": "Ожидает проверки",
    "waiting_moderation": "Ожидает модерации",
    "rejected": "Отклонён",
    "approved": "Принят",
}
QUEUE_STATUSES = ("waiting_approved", "waiting_moderation")
MODERATION_STATUSES = ("waiting_register", "waiting_approved", "waiting_moderation", "rejected")
REQUIRED_DOCUMENT_TYPES = (
    "PASSPORT_FRONT",
    "PASSPORT_REGISTRATION",
    "DRIVER_LICENSE_FRONT",
    "DRIVER_LICENSE_BACK",
    "STS_FRONT",
    "STS_BACK",
)


def _is_moderator(request):
    return request.user.is_authenticated and (
        request.user.is_superuser
        or request.user.groups.filter(name__in=("Admin", "Operator")).exists()
    )


def _moderation_context(request):
    from django.contrib import admin

    count = DriverProfile.objects.filter(status__in=QUEUE_STATUSES).count()
    return {
        "site_header": admin.site.site_header,
        "queue_count": count,
        "status_labels": STATUS_LABELS,
    }


def _annotated_profiles():
    phone_query = User.objects.filter(id=models.OuterRef("user_id")).values("phone")[:1]
    email_query = User.objects.filter(id=models.OuterRef("user_id")).values("email")[:1]
    return DriverProfile.objects.exclude(
        status__in=(DriverProfile.STATUS_APPROVED, "waiting_register", "rejected")
    ).annotate(
        user_phone=Subquery(phone_query),
        user_email=Subquery(email_query),
        status_order=Case(
            When(status="waiting_moderation", then=Value(0)),
            When(status="waiting_approved", then=Value(1)),
            When(status="waiting_register", then=Value(2)),
            When(status="rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        ),
    )


def _status_url_params(request):
    params = {}
    if request.GET.get("q"):
        params["q"] = request.GET["q"]
    if request.GET.get("status"):
        params["status"] = request.GET["status"]
    return urlencode(params)


def moderation_list(request):
    if not _is_moderator(request):
        raise Http404()

    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in ("waiting_register", "rejected"):
        profiles = DriverProfile.objects.filter(status=status).annotate(
            user_phone=Subquery(User.objects.filter(id=models.OuterRef("user_id")).values("phone")[:1]),
            user_email=Subquery(User.objects.filter(id=models.OuterRef("user_id")).values("email")[:1]),
            status_order=Value(2, output_field=IntegerField()),
        )
    else:
        profiles = _annotated_profiles()
        if status in MODERATION_STATUSES:
            profiles = profiles.filter(status=status)
    if query:
        user_ids = User.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        ).values("id")
        profiles = profiles.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(user_id__in=user_ids)
        )

    profiles = profiles.order_by("status_order", "-updated_at", "-id")
    return render(
        request,
        "admin_drivers/moderation_list.html",
        {
            **_moderation_context(request),
            "profiles": profiles,
            "selected_status": status,
            "search_query": query,
            "status_choices": [(key, STATUS_LABELS[key]) for key in MODERATION_STATUSES],
            "query_params": _status_url_params(request),
        },
    )


def moderation_detail(request, profile_id: int):
    if not _is_moderator(request):
        raise Http404()

    profile = get_object_or_404(DriverProfile, pk=profile_id)
    user = User.objects.filter(id=profile.user_id).first()
    if not user:
        raise Http404("User not found")

    form = DriverModerationForm(instance=profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save":
            form = DriverModerationForm(request.POST, instance=profile)
            if form.is_valid():
                with transaction.atomic():
                    form.save_related_data()
                messages.success(request, "Профиль водителя сохранён.")
                return HttpResponseRedirect(request.path)
        elif action in ("approved", "rejected"):
            reason_ids = [int(value) for value in request.POST.getlist("moderation_info_ids") if value.isdigit()]
            success = api_client.moderate_driver(
                profile.id,
                action,
                reason_ids,
                request.user.id,
            )
            if success:
                messages.success(request, "Решение модерации сохранено.")
                return HttpResponseRedirect(request.path)
            messages.error(request, "Не удалось сохранить решение через backend. Проверьте MODERATION_INTERNAL_TOKEN.")
        elif action == "block":
            user.is_active = False
            user.save(update_fields=["is_active"])
            messages.success(request, "Пользователь заблокирован.")
            return HttpResponseRedirect(request.path)
        elif action == "delete":
            with transaction.atomic():
                _delete_driver_related_records(profile)
                profile.delete()
            messages.success(request, "Профиль водителя удалён.")
            return HttpResponseRedirect(reverse("driver-moderation-list"))
        else:
            form = DriverModerationForm(instance=profile)
    else:
        form = DriverModerationForm(instance=profile)

    cars = list(Car.objects.filter(driver_profile_id=profile.id).order_by("id"))
    car_ids = [car.id for car in cars]
    documents = DriverDocument.objects.filter(driver_profile_id=profile.id).order_by("doc_type", "-created_at")
    car_photos = list(CarPhoto.objects.filter(car_id__in=car_ids).order_by("car_id", "type")) if car_ids else []
    photos_by_car = defaultdict(list)
    for photo in car_photos:
        photos_by_car[photo.car_id].append(photo)
    cars_data = [{"car": car, "photos": photos_by_car.get(car.id, [])} for car in cars]
    moderation_rows = DriverProfileModeration.objects.filter(
        driver_profile_id=profile.id
    ).select_related("driver_moderation_info")
    reasons = [row.driver_moderation_info for row in moderation_rows]
    all_reasons = DriverModerationInfo.objects.all().order_by("code")
    warning_documents = documents.exclude(status="approved")
    uploaded_document_types = set(documents.values_list("doc_type", flat=True))
    missing_documents = [doc_type for doc_type in REQUIRED_DOCUMENT_TYPES if doc_type not in uploaded_document_types]
    document_groups = defaultdict(list)
    for document in documents:
        document_groups[document.doc_type].append(document)
    return render(
        request,
        "admin_drivers/moderation_detail.html",
        {
            **_moderation_context(request),
            "profile": profile,
            "user": user,
            "form": form,
            "cars": cars,
            "cars_data": cars_data,
            "documents": documents,
            "document_groups": sorted(document_groups.items()),
            "reasons": reasons,
            "all_reasons": all_reasons,
            "warning_documents": warning_documents,
            "missing_documents": missing_documents,
            "status_label": STATUS_LABELS.get(profile.status, profile.status),
        },
    )


def _delete_driver_related_records(profile):
    car_ids = list(Car.objects.filter(driver_profile_id=profile.pk).values_list("id", flat=True))
    DriverLocation.objects.filter(driver_profile_id=profile.pk).delete()
    DriverDocument.objects.filter(driver_profile_id=profile.pk).delete()
    RideDriversRequest.objects.filter(driver_profile_id=profile.pk).delete()
    DriverProfileModeration.objects.filter(driver_profile_id=profile.pk).delete()
    Ride.objects.filter(driver_profile_id=profile.pk).update(driver_profile_id=None)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM driver_ratings WHERE driver_profile_id = %s", [profile.pk])
    if car_ids:
        CarPhoto.objects.filter(car_id__in=car_ids).delete()
        RideDriversRequest.objects.filter(car_id__in=car_ids).delete()
        Car.objects.filter(id__in=car_ids).delete()
