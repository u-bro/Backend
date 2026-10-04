from django.db import models

from admin_users.models import User


class SafeJSONField(models.JSONField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None

        # PostgreSQL driver may already deserialize JSON/JSONB.
        if isinstance(value, (dict, list, int, float, bool)):
            return value

        return super().from_db_value(value, expression, connection)


class SupportConversation(models.Model):
    SOURCE_CHOICES = (
        ("APP", "Приложение"),
        ("LANDING", "Лендинг"),
        ("DIRECT", "Прямой вход"),
    )

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    user = models.ForeignKey(
        User,
        models.DO_NOTHING,
        db_column="user_id",
        related_name="support_conversations",
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    max_user_id = models.BigIntegerField(verbose_name="Номер пользователя в MAX", null=True, blank=True)
    max_chat_id = models.BigIntegerField(verbose_name="Номер чата в MAX")
    status = models.CharField(verbose_name="Статус", max_length=10)
    source = models.CharField(verbose_name="Источник", max_length=10, choices=SOURCE_CHOICES)
    last_inbound_message_id = models.BigIntegerField(verbose_name="Номер последнего входящего сообщения", null=True, blank=True)
    last_read_message_id = models.BigIntegerField(verbose_name="Номер последнего прочитанного сообщения", null=True, blank=True)
    last_inbound_at = models.DateTimeField(verbose_name="Последнее входящее сообщение", null=True, blank=True)
    last_outbound_at = models.DateTimeField(verbose_name="Последнее исходящее сообщение", null=True, blank=True)
    closed_at = models.DateTimeField(verbose_name="Дата закрытия", null=True, blank=True)
    closed_by = models.CharField(verbose_name="Кем закрыто", max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания")
    updated_at = models.DateTimeField(verbose_name="Дата изменения")

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

    @property
    def contact_phone(self):
        if self.user_id and self.user:
            return self.user.phone or "—"
        return "—"

    @property
    def contact_label(self):
        if self.user_id and self.user:
            name = " ".join(filter(None, (self.user.first_name, self.user.last_name)))
            return name or self.user.phone or "Пользователь приложения"
        if self.source == "LANDING":
            return "Гость лендинга"
        if self.source == "DIRECT":
            return "Пользователь MAX"
        return "Гость MAX"


class SupportMessage(models.Model):
    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    conversation = models.ForeignKey(
        SupportConversation,
        models.DO_NOTHING,
        db_column="conversation_id",
        related_name="support_messages",
        verbose_name="Обращение",
    )
    sender_type = models.CharField(verbose_name="Тип отправителя", max_length=10)
    user = models.ForeignKey(User, models.DO_NOTHING, db_column="user_id", null=True, blank=True, verbose_name="Пользователь")
    text = models.TextField(verbose_name="Текст", null=True, blank=True)
    external_message_id = models.CharField(verbose_name="Внешний номер сообщения", max_length=255, null=True, blank=True)
    message_type = models.CharField(verbose_name="Тип сообщения", max_length=20)
    delivery_status = models.CharField(verbose_name="Статус доставки", max_length=10)
    delivery_error = models.CharField(verbose_name="Ошибка доставки", max_length=500, null=True, blank=True)
    idempotency_key = models.CharField(verbose_name="Ключ защиты от повторной операции", max_length=100, null=True, blank=True)
    operator_name = models.CharField(verbose_name="Имя оператора", max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания")

    class Meta:
        managed = False
        db_table = "support_messages"
        ordering = ("created_at", "id")
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"


class SupportMessageAttachment(models.Model):
    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    message = models.ForeignKey(
        SupportMessage,
        models.DO_NOTHING,
        db_column="message_id",
        related_name="attachments",
        verbose_name="Сообщение",
    )
    attachment_type = models.CharField(verbose_name="Тип вложения", max_length=30)
    file_name = models.CharField(verbose_name="Имя файла", max_length=500, null=True, blank=True)
    mime_type = models.CharField(verbose_name="Тип содержимого файла", max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(verbose_name="Размер файла", null=True, blank=True)
    provider_url = models.TextField(verbose_name="Ссылка у поставщика", null=True, blank=True)
    provider_metadata = SafeJSONField(verbose_name="Данные поставщика", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания")

    class Meta:
        managed = False
        db_table = "support_message_attachments"
        verbose_name = "Вложение поддержки"
        verbose_name_plural = "Вложения поддержки"
