from django.contrib import admin

from .models import RideDriversRequest


@admin.register(RideDriversRequest)
class RideDriversRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id",
        "driver_profile_id",
        "car_id",
        "status",
        "eta",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("ride_id", "driver_profile_id", "car_id")
    readonly_fields = ("id", "created_at", "updated_at")
