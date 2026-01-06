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
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("from_status", "to_status", "actor_role", "created_at")
    search_fields = ("reason",)

    readonly_fields = ('id', 'created_at')
