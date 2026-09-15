from utils.admin_permissions import has_service_permission
from django.contrib import admin

from .models import Role
from utils.admin_stats_admin import EntityStatsAdminMixin


@admin.register(Role)
class RoleAdmin(EntityStatsAdminMixin, admin.ModelAdmin):
    list_display = ("id", "code", "name", "description", "created_at", "updated_at")
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("created_at", "updated_at")
    search_fields = ("code", "name", "description")

    readonly_fields = ('id', 'created_at', 'updated_at')

    def has_add_permission(self, request): 
        return False

    def has_change_permission(self, request, obj=None): 
        return has_service_permission(request.user, f"{self.opts.app_label}.change_{self.opts.model_name}", ("Admin",))

    def has_delete_permission(self, request, obj=None):  
        return False

# Register staff access roles separately from the backend's roles table.
from . import access_admin  # noqa: E402, F401
