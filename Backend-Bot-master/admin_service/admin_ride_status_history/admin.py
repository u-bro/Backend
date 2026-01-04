from django.contrib import admin

from .models import RideStatusHistory


@admin.register(RideStatusHistory)
class RideStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id",
        "from_status",
        "to_status",
        "changed_by",
        "actor_role",
        "created_at",
    )
    list_editable = ()  # Read-only: has_change_permission=False
    list_filter = ("from_status", "to_status", "actor_role", "created_at")
    search_fields = ("reason",)

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
