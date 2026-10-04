from django.db import models


class ChatMessage(models.Model):
    class Meta:
        db_table = 'chat_messages'
        managed = False
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чатов'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    ride_id = models.IntegerField(verbose_name="Номер поездки", null=True, blank=True)
    text = models.TextField(verbose_name="Текст", null=True, blank=True)
    sender_id = models.IntegerField(verbose_name="Номер отправителя", null=True, blank=True)
    receiver_id = models.IntegerField(verbose_name="Номер получателя", null=True, blank=True)
    message_type = models.CharField(verbose_name="Тип сообщения", max_length=50, null=True, blank=True)
    attachments = models.JSONField(verbose_name="Вложения", null=True, blank=True)
    is_moderated = models.BooleanField(verbose_name="Проверено модератором", default=False)
    is_read = models.BooleanField(verbose_name="Прочитано", default=False)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    edited_at = models.DateTimeField(verbose_name="Дата редактирования", null=True, blank=True)
    deleted_at = models.DateTimeField(verbose_name="Дата удаления", null=True, blank=True)

    def __str__(self) -> str:
        return f"Сообщение №{self.id}"
