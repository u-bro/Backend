from django.contrib import admin

from .models import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "admin_user_id",
        "action",
        "target_type",
        "target_id",
        "created_at",
    )
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("action", "target_type")
    readonly_fields = ("admin_user_id", "action", "target_type", "target_id", "old_values", "new_values", "ip_address", "user_agent", "created_at")

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
