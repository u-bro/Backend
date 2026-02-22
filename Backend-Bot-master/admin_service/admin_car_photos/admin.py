from django.contrib import admin

from .models import CarPhoto


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "car_id",
        "type",
        "description",
        "photo_url",
        "created_at",
        "updated_at",
    )
    list_filter = ("type", "created_at")
    search_fields = ("car_id", "type", "description")
    list_per_page = 25

    def has_add_permission(self, request):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
