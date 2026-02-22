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
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("ride_id", "driver_profile_id", "car_id")
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
