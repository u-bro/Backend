from django.contrib import admin

from .models import InAppNotification


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "type",
        "title",
        "read_at",
        "dedup_key",
        "created_at",
    )
    list_filter = ("type", "read_at", "created_at")
    search_fields = ("title", "message", "dedup_key", "user_id")
    readonly_fields = ("id", "created_at")
