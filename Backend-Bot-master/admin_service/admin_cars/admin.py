from django.contrib import admin

from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
        "model",
        "number",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at",)
    search_fields = ("model", "number", "driver_profile_id")
    readonly_fields = ("id", "created_at", "updated_at")
