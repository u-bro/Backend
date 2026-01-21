from django.contrib import admin

from .models import RefreshToken


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "token",
        "expires_at",
        "revoked_at",
        "created_at",
    )
    list_filter = ("expires_at", "revoked_at", "created_at")
    search_fields = ("token", "user_id")
    readonly_fields = ("id", "created_at")
