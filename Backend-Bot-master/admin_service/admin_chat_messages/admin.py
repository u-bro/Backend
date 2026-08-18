from django.contrib import admin

from .models import ChatMessage
from utils.admin_links import ride_link, user_link


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id_link",
        "sender_id_link",
        "receiver_id_link",
        "message_type",
        "is_moderated",
        "is_read",
        "created_at",
        "edited_at",
    )
    list_editable = ("message_type", "is_moderated", "is_read", "created_at", "edited_at")
    list_filter = ("message_type", "is_moderated", "is_read", "created_at")
    search_fields = ("text",)

    list_per_page = 25

    readonly_fields = ('id', 'created_at', 'edited_at', 'deleted_at', 'ride_id_link', 'sender_id_link', 'receiver_id_link')

    @admin.display(description="Ride ID", ordering="ride_id")
    def ride_id_link(self, obj):
        return ride_link(getattr(obj, "ride_id", None))

    @admin.display(description="Sender ID", ordering="sender_id")
    def sender_id_link(self, obj):
        return user_link(getattr(obj, "sender_id", None))

    @admin.display(description="Receiver ID", ordering="receiver_id")
    def receiver_id_link(self, obj):
        return user_link(getattr(obj, "receiver_id", None))

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_moderated:
            readonly.extend(['text', 'attachments'])
        return readonly
