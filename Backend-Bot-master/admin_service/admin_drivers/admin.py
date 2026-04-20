from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from utils.api_client import api_client
from utils.schema_choices import RIDE_CLASS_CHOICES

from admin_car_photos.models import CarPhoto
from admin_cars.models import Car
from admin_driver_documents.models import DriverDocument
from admin_driver_locations.models import DriverLocation
from admin_ride_drivers_requests.models import RideDriversRequest
from admin_rides.models import Ride
from .models import DriverModerationInfo, DriverProfile, DriverProfileModeration


class DriverProfileAdminForm(forms.ModelForm):
    classes_allowed = forms.MultipleChoiceField(
        choices=RIDE_CLASS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = DriverProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classes_allowed = getattr(self.instance, "classes_allowed", None)
        if isinstance(classes_allowed, list):
            self.initial["classes_allowed"] = classes_allowed

    def clean_user_id(self):
        user_id = self.cleaned_data.get("user_id")
        if user_id is None:
            return user_id

        existing = (
            DriverProfile.objects.filter(user_id=user_id)
            .exclude(pk=getattr(self.instance, "pk", None))
            .only("id")
            .first()
        )
        if existing:
            raise ValidationError(
                f"Профиль водителя для user_id={user_id} уже существует (id профиля: {existing.id})."
            )
        return user_id

    def clean_classes_allowed(self):
        return self.cleaned_data.get("classes_allowed", [])


class DriverProfileChangelistForm(forms.ModelForm):
    classes_allowed = forms.MultipleChoiceField(
        choices=RIDE_CLASS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = DriverProfile
        fields = ("status", "approved", "classes_allowed")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classes_allowed = getattr(self.instance, "classes_allowed", None)
        if isinstance(classes_allowed, list):
            self.initial["classes_allowed"] = classes_allowed

    def clean_classes_allowed(self):
        return self.cleaned_data.get("classes_allowed", [])


@admin.register(DriverModerationInfo)
class DriverModerationInfoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "message",
        "created_at",
    )
    search_fields = ("code", "message")


class DriverProfileModerationInline(admin.TabularInline):
    model = DriverProfileModeration
    extra = 0
    autocomplete_fields = ("driver_moderation_info",)
    fields = ("driver_moderation_info", "created_at")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()


@admin.register(DriverProfileModeration)
class DriverProfileModerationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile",
        "driver_moderation_info",
        "created_at",
    )
    list_filter = ("driver_moderation_info",)
    search_fields = ("driver_profile__id", "driver_profile__user_id", "driver_moderation_info__code")
    autocomplete_fields = ("driver_profile", "driver_moderation_info")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    form = DriverProfileAdminForm
    inlines = (DriverProfileModerationInline,)
    list_display = (
        "id",
        "user_id",
        "user_phone",
        "display_name",
        "first_name",
        "last_name",
        "status",
        "classes_allowed",
        "moderation_reasons",
        "approved",
        "user_is_active",
        "rating_avg",
        "created_at",
        "updated_at",
    )
    list_per_page = 25
    list_editable = tuple(
        [f for f in list_display if f != 'id' and any(f == fld.name for fld in DriverProfile._meta.fields) and f not in ['license_number', 'license_category', 'license_issued_at', 'license_expires_at', 'experience_years']]
    )
    list_filter = ("approved", "status")
    search_fields = ("user_id", "first_name", "last_name", "_user_phone")
    actions = ["approve_drivers", "reject_drivers", "block_drivers", "unblock_drivers"]

    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at')

    def get_changelist_form(self, request, **kwargs):
        kwargs["form"] = DriverProfileChangelistForm
        return super().get_changelist_form(request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            from admin_users.models import User
            phone_sq = User.objects.filter(id=OuterRef("user_id")).values("phone")[:1]
            return qs.annotate(_user_phone=Subquery(phone_sq))
        except Exception:
            return qs

    def display_name(self, obj):
        name_parts = [p for p in [getattr(obj, 'first_name', None), getattr(obj, 'last_name', None)] if p]
        return " ".join(name_parts) if name_parts else f"Driver {obj.id}"

    def user_phone(self, obj):
        phone = getattr(obj, "_user_phone", None)
        if phone:
            return phone
        try:
            from admin_users.models import User
            user = User.objects.filter(id=obj.user_id).only("phone").first()
            return getattr(user, "phone", None) or ""
        except Exception:
            return ""
    user_phone.short_description = "Phone"

    def moderation_reasons(self, obj):
        try:
            items = obj.moderation_info.all()
            return ", ".join(str(i) for i in items)
        except Exception:
            return ""
    moderation_reasons.short_description = "Moderation reasons"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.approved:
            readonly.extend(['license_number', 'license_category', 'license_issued_at', 'license_expires_at', 'experience_years'])
        return readonly

    def has_add_permission(self, request): 
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):  
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):  
        return request.user.groups.filter(name='Admin').exists()

    def user_is_active(self, obj):  
        try:
            from admin_users.models import User
            user = User.objects.filter(id=obj.user_id).first()
            return "Active" if user and user.is_active else "Blocked"
        except:
            return "Unknown"
    user_is_active.short_description = "User Status"

    def save_model(self, request, obj, form, change):
        try:
            if obj.status == DriverProfile.STATUS_APPROVED:
                obj.approved = True
                if not obj.approved_at:
                    obj.approved_at = timezone.now()
            super().save_model(request, obj, form, change)
            if not change and obj.pk:
                DriverLocation.objects.get_or_create(
                    driver_profile_id=obj.pk,
                    defaults={"status": "offline"},
                )
            return
        except IntegrityError:
            existing = DriverProfile.objects.filter(user_id=getattr(obj, "user_id", None)).only("id").first()
            if existing:
                form.add_error(
                    "user_id",
                    ValidationError(
                        f"Профиль водителя для user_id={obj.user_id} уже существует (id профиля: {existing.id})."
                    ),
                )
                return
            raise

    def delete_model(self, request, obj):
        self._delete_related_records(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self._delete_related_records(obj)
        super().delete_queryset(request, queryset)

    def _delete_related_records(self, obj):
        car_ids = list(Car.objects.filter(driver_profile_id=obj.pk).values_list("id", flat=True))

        DriverLocation.objects.filter(driver_profile_id=obj.pk).delete()
        DriverDocument.objects.filter(driver_profile_id=obj.pk).delete()
        RideDriversRequest.objects.filter(driver_profile_id=obj.pk).delete()
        DriverProfileModeration.objects.filter(driver_profile_id=obj.pk).delete()
        Ride.objects.filter(driver_profile_id=obj.pk).update(driver_profile_id=None)
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM driver_ratings WHERE driver_profile_id = %s", [obj.pk])

        if car_ids:
            CarPhoto.objects.filter(car_id__in=car_ids).delete()
            RideDriversRequest.objects.filter(car_id__in=car_ids).delete()
            Car.objects.filter(id__in=car_ids).delete()

    def approve_drivers(self, request, queryset):  
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        approved_by = self._resolve_backend_user_id(request)
        for driver in queryset:
            driver.approved = True
            driver.status = DriverProfile.STATUS_APPROVED
            driver.approved_by = approved_by
            driver.approved_at = timezone.now()
            driver.save()
            count += 1
        self.message_user(request, f"Approved {count} drivers", messages.SUCCESS)

    def reject_drivers(self, request, queryset):  
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        approved_by = self._resolve_backend_user_id(request)
        for driver in queryset:
            driver.approved = False
            driver.approved_by = approved_by
            driver.approved_at = timezone.now()
            driver.save()
            count += 1
        self.message_user(request, f"Rejected {count} drivers", messages.SUCCESS)

    def block_drivers(self, request, queryset):  
        if not request.user.groups.filter(name='Admin').exists():
            self.message_user(request, "Only Admin can block drivers", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            from admin_users.models import User
            user = User.objects.filter(id=driver.user_id).first()
            if user:
                user.is_active = False
                user.save()
                count += 1
        self.message_user(request, f"Blocked {count} drivers", messages.SUCCESS)

    def unblock_drivers(self, request, queryset): 
        if not request.user.groups.filter(name='Admin').exists():
            self.message_user(request, "Only Admin can unblock drivers", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            from admin_users.models import User
            user = User.objects.filter(id=driver.user_id).first()
            if user:
                user.is_active = True
                user.save()
                count += 1
        self.message_user(request, f"Unblocked {count} drivers", messages.SUCCESS)
