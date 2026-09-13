from django.contrib import admin

from .models import Commission
from utils.admin_stats_admin import EntityStatsAdminMixin


@admin.register(Commission)
class CommissionAdmin(EntityStatsAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "percentage",
        "fixed_amount",
        "currency",
        "valid_from",
        "valid_to",
        "created_at",
    )
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("valid_from", "valid_to", "created_at")
    search_fields = ("name", "currency")

    readonly_fields = ('id', 'created_at')
