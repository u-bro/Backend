from django.contrib import admin

from .models import DriverDocument


@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
        "doc_type",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_editable = ()  # Read-only: has_change_permission=False
    list_filter = ("doc_type", "status", "created_at")
    search_fields = ("doc_type", "file_url")

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
