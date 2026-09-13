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
        return request.user.groups.filter(name='Admin').exists()

    def has_delete_permission(self, request, obj=None):  
        return False
