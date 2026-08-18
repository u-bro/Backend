from django.contrib import admin
from django.utils.html import format_html

from .models import CarPhoto
from utils.admin_links import safe_external_url


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
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
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
