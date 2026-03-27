from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import DriverDocument
from utils.s3_storage import s3_storage


@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver_profile_id",
        "doc_type",
        "document_preview",
        "document_link",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_editable = ("status", "reviewed_by", "reviewed_at")
    list_filter = ("doc_type", "status", "created_at")
    search_fields = ("doc_type", "file_bucket_key")

    readonly_fields = ("id", "created_at", "document_preview", "document_link")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:document_id>/preview/",
                self.admin_site.admin_view(self.preview_document_view),
                name="admin_driver_document_preview",
            ),
        ]
        return custom_urls + urls

    @xframe_options_sameorigin
    def preview_document_view(self, request, document_id: int):
        document = self.get_object(request, document_id)
        if document is None or not document.file_bucket_key:
            raise Http404("Document not found")

        try:
            content, content_type, content_disposition = s3_storage.get_object(document.file_bucket_key)
        except FileNotFoundError:
            raise Http404("Document not found")

        return HttpResponse(
            content,
            content_type=content_type,
            headers={"Content-Disposition": content_disposition},
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'approved':
            readonly.extend(["doc_type", "file_bucket_key"])
        return readonly

    @admin.display(description="Превью")
    def document_preview(self, obj):
        if not obj.file_bucket_key:
            return "Нет файла"

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '<img src="{}" alt="document preview" style="max-height: 120px; max-width: 120px; object-fit: contain; border: 1px solid #ddd; background: #fff;" />'
            "</a>",
            reverse("admin:admin_driver_document_preview", args=[obj.id]),
            reverse("admin:admin_driver_document_preview", args=[obj.id]),
        )

    @admin.display(description="Файл")
    def document_link(self, obj):
        if not obj.file_bucket_key:
            return "Нет файла"

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Открыть</a><br><code>{}</code>',
            reverse("admin:admin_driver_document_preview", args=[obj.id]),
            obj.file_bucket_key,
        )
