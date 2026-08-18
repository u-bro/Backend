from django.contrib import admin

from .models import DriverLocation
from utils.admin_links import driver_profile_link


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id_link",
        "status",
        "latitude",
        "longitude",
        "last_seen_at",
        "created_at",
    )
    list_editable = ("status", "latitude", "longitude")
    list_filter = ("status", "created_at")
    search_fields = ("driver_profile_id",)
    list_per_page = 25
    readonly_fields = ("id", "created_at", "last_seen_at", "driver_profile_id_link")

    @admin.display(description="Driver profile ID", ordering="driver_profile_id")
    def driver_profile_id_link(self, obj):
        return driver_profile_link(getattr(obj, "driver_profile_id", None))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
