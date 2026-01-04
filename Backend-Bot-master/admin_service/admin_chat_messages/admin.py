from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id",
        "sender_id",
        "receiver_id",
        "message_type",
        "is_moderated",
        "created_at",
        "edited_at",
    )
    list_editable = ()  # Read-only: has_change_permission=False
    list_filter = ("message_type", "is_moderated", "created_at")
    search_fields = ("text",)

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
