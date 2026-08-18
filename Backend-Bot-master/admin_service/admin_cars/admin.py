from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import Car
from admin_car_photos.models import CarPhoto
from admin_drivers.models import DriverProfile
from utils.admin_links import driver_profile_link, safe_external_url


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    change_form_template = "admin/admin_cars/car/change_form.html"
    list_display = (
        "id",
        "driver_profile_id_link",
        "model",
        "number",
        "region",
        "vin",
        "year",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("number", "vin", "model", "driver_profile_id")
    list_per_page = 25
    readonly_fields = ("driver_profile_id_link", "photo_gallery")
    fieldsets = (
        ("Автомобиль", {"fields": ("driver_profile_id", "driver_profile_id_link", "model", "number", "region", "vin", "year")}),
        ("Фотографии", {"fields": ("photo_gallery",)}),
        ("Служебная информация", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Driver profile ID", ordering="driver_profile_id")
    def driver_profile_id_link(self, obj):
        return driver_profile_link(getattr(obj, "driver_profile_id", None))

    @admin.display(description="Фотографии автомобиля")
    def photo_gallery(self, obj):
        if not obj or not obj.pk:
            return "Сохраните автомобиль, чтобы добавить фотографии."

        photos = CarPhoto.objects.filter(car_id=obj.pk).order_by("type", "id")
        if not photos:
            return "Фотографии не загружены."

        cards = format_html_join(
            "",
            '<article class="car-photo-card">'
            '<a href="{}" target="_blank" rel="noopener"><img src="{}" alt="{}"></a>'
            '<div><strong>{}</strong><span>{}</span><small>Статус: {}</small></div>'
            "</article>",
            (
                (
                    safe_external_url(photo.photo_url),
                    safe_external_url(photo.photo_url),
                    photo.type or "Фото автомобиля",
                    photo.type or "Фото",
                    photo.description or "Без описания",
                    photo.status or "—",
                )
                for photo in photos
                if safe_external_url(photo.photo_url)
            )
        )
        if not cards:
            return "У фотографий отсутствуют URL."
        return format_html('<div class="car-photo-gallery">{}</div>', cards)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and getattr(obj, "driver_profile_id", None) and getattr(obj, "id", None):
            DriverProfile.objects.filter(id=obj.driver_profile_id).update(current_car_id=obj.id)

    def has_add_permission(self, request):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
