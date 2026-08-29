from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import CarPhoto
from admin_cars.models import Car
from admin_drivers.models import DriverProfile
from utils.admin_links import safe_external_url


class CarPhotoAdminForm(forms.ModelForm):
    class Meta:
        model = CarPhoto
        fields = "__all__"

    def clean_car_id(self):
        car_id = self.cleaned_data["car_id"]
        profile_id = Car.objects.filter(id=car_id).values_list(
            "driver_profile_id", flat=True
        ).first()
        if profile_id and DriverProfile.objects.filter(id=profile_id, approved=True).exists():
            raise ValidationError("Нельзя изменять фото автомобиля одобренного водителя.")
        return car_id


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
    form = CarPhotoAdminForm
    list_display = (
        "id",
        "car_id",
        "type",
        "description",
        "photo_preview",
        "photo_link",
        "created_at",
        "updated_at",
    )
    list_filter = ("type", "created_at")
    search_fields = ("car_id", "type", "description")
    list_per_page = 25
    readonly_fields = ("photo_preview", "photo_link")

    @staticmethod
    def _profile_is_approved(obj):
        if not obj or not getattr(obj, "car_id", None):
            return False
        profile_id = Car.objects.filter(id=obj.car_id).values_list(
            "driver_profile_id", flat=True
        ).first()
        return bool(
            profile_id
            and DriverProfile.objects.filter(id=profile_id, approved=True).exists()
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if self._profile_is_approved(obj):
            readonly.extend("car_id type description photo_url status".split())
        return tuple(dict.fromkeys(readonly))

    @admin.display(description="Превью")
    def photo_preview(self, obj):
        photo_url = safe_external_url(obj.photo_url)
        if not photo_url:
            return "Нет фото"

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '<img src="{}" alt="car photo" style="max-height: 120px; max-width: 120px; object-fit: cover; border: 1px solid #ddd; background: #fff;" />'
            "</a>",
            photo_url,
            photo_url,
        )

    @admin.display(description="Файл")
    def photo_link(self, obj):
        photo_url = safe_external_url(obj.photo_url)
        if not photo_url:
            return "Нет фото"

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Открыть</a>',
            photo_url,
        )

    def has_add_permission(self, request):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):
        allowed = request.user.groups.filter(name__in=['Admin', 'Operator']).exists()
        return allowed and not self._profile_is_approved(obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists() and not self._profile_is_approved(obj)
