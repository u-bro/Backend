from django.contrib import admin

from .models import DriverLocation


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
        "status",
        "latitude",
        "longitude",
        "provider",
        "last_seen_at",
        "created_at",
    )
    list_filter = ("status", "provider", "created_at")
    search_fields = ("driver_profile_id",)
    readonly_fields = ("id", "created_at")
