from django.contrib import admin

from .models import PhoneVerification


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "phone",
        "status",
        "is_registred",
        "attempts",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "is_registred", "created_at")
    search_fields = ("phone", "user_id")
    readonly_fields = ("id", "created_at")
