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
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("action", "target_type")

    def has_add_permission(self, request): 
        return False

    def has_change_permission(self, request, obj=None):  
        return False

    def has_delete_permission(self, request, obj=None): 
        return False
