from django.contrib import admin

from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "display_name",
        "first_name",
        "last_name",
        "approved",
        "documents_status",
        "rating_avg",
        "created_at",
        "updated_at",
    )
    list_filter = ("approved", "documents_status")
    search_fields = ("display_name", "first_name", "last_name")

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
