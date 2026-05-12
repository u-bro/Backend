from django.contrib import admin

from .models import Car
from admin_drivers.models import DriverProfile


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
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
