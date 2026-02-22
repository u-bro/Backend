from django.contrib import admin

from .models import Car


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

    def has_add_permission(self, request):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Admin').exists()
