from django.contrib import admin

from .models import RideStatusHistory
from utils.admin_links import ride_link


@admin.register(RideStatusHistory)
class RideStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id_link",
        "from_status",
        "to_status",
        "changed_by",
        "actor_role",
        "created_at",
    )
    list_editable = ("from_status", "to_status", "changed_by", "actor_role", "created_at")
    list_filter = ("from_status", "to_status", "actor_role", "created_at")
    search_fields = ("reason",)

    readonly_fields = ('id', 'created_at', 'ride_id_link')

    @admin.display(description="Ride ID", ordering="ride_id")
    def ride_id_link(self, obj):
        return ride_link(getattr(obj, "ride_id", None))
