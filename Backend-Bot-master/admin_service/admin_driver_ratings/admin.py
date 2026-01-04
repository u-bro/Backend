from django.contrib import admin

from .models import DriverRating


@admin.register(DriverRating)
class DriverRatingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
        "client_id",
        "ride_id",
        "rate",
        "comment",
        "created_at",
    )
    list_editable = ()  # Read-only: has_change_permission=False
    list_filter = ("rate", "created_at")
    search_fields = ("comment",)

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
