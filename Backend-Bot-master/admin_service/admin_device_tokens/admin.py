from django.contrib import admin

from .models import DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "platform",
        "token",
        "created_at",
    )
    list_filter = ("platform", "created_at")
    search_fields = ("token", "user_id")
    readonly_fields = ("id", "created_at")
