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
        "last_seen_at",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("driver_profile_id",)
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
