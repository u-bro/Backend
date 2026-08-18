from django.contrib import admin

from .models import RideDriversRequest
from utils.admin_links import driver_profile_link, ride_link


@admin.register(RideDriversRequest)
class RideDriversRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id_link",
        "driver_profile_id_link",
        "car_id",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("ride_id", "driver_profile_id", "car_id")
    list_per_page = 25
    readonly_fields = ("ride_id_link", "driver_profile_id_link")

    @admin.display(description="Ride ID", ordering="ride_id")
    def ride_id_link(self, obj):
        return ride_link(getattr(obj, "ride_id", None))

    @admin.display(description="Driver profile ID", ordering="driver_profile_id")
    def driver_profile_id_link(self, obj):
        return driver_profile_link(getattr(obj, "driver_profile_id", None))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
