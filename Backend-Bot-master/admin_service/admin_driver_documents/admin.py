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
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("doc_type", "status", "created_at")
    search_fields = ("doc_type", "file_url")

    readonly_fields = ('id', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'approved':
            readonly.extend(['doc_type', 'file_url'])
        return readonly
