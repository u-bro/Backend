from django.db import models

from admin_users.models import User


class SupportConversation(models.Model):
    SOURCE_CHOICES = (
        ("APP", "Приложение"),
        ("LANDING", "Лендинг"),
        ("DIRECT", "Прямой вход"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        models.DO_NOTHING,
        db_column="user_id",
        related_name="support_conversations",
        null=True,
        blank=True,
    )
    max_user_id = models.BigIntegerField(null=True, blank=True)
    max_chat_id = models.BigIntegerField()
    status = models.CharField(max_length=10)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    last_inbound_message_id = models.BigIntegerField(null=True, blank=True)
    last_read_message_id = models.BigIntegerField(null=True, blank=True)
    last_inbound_at = models.DateTimeField(null=True, blank=True)
    last_outbound_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "support_conversations"
        verbose_name = "Диалог поддержки"
        verbose_name_plural = "Диалоги поддержки"

    @property
    def display_name(self):
        if self.user_id and self.user:
            return " ".join(filter(None, (self.user.first_name, self.user.last_name))) or self.user.phone
        return None


class SupportMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(
        SupportConversation,
        models.DO_NOTHING,
        db_column="conversation_id",
        related_name="support_messages",
    )
    sender_type = models.CharField(max_length=10)
    user = models.ForeignKey(User, models.DO_NOTHING, db_column="user_id", null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    external_message_id = models.CharField(max_length=255, null=True, blank=True)
    message_type = models.CharField(max_length=20)
    delivery_status = models.CharField(max_length=10)
    delivery_error = models.CharField(max_length=500, null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True)
    operator_name = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "support_messages"
        ordering = ("created_at", "id")
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"


class SupportMessageAttachment(models.Model):
    id = models.BigAutoField(primary_key=True)
    message = models.ForeignKey(
        SupportMessage,
        models.DO_NOTHING,
        db_column="message_id",
        related_name="attachments",
    )
    attachment_type = models.CharField(max_length=30)
    file_name = models.CharField(max_length=500, null=True, blank=True)
    mime_type = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    provider_url = models.TextField(null=True, blank=True)
    provider_metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "support_message_attachments"
        verbose_name = "Вложение поддержки"
        verbose_name_plural = "Вложения поддержки"
