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
    list_editable = ()  # has_change_permission=False, no editing allowed
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("action", "target_type")
    # Allow editing of audit records via admin (if needed)

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
