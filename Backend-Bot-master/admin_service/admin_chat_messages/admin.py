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
        "is_read",
        "created_at",
        "edited_at",
    )
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("message_type", "is_moderated", "is_read", "created_at")
    search_fields = ("text",)

    list_per_page = 25

    readonly_fields = ('id', 'created_at', 'edited_at', 'deleted_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_moderated:
            readonly.extend(['text', 'attachments'])
        return readonly
