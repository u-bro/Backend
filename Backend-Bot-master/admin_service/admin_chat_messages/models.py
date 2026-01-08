from django.db import models


class ChatMessage(models.Model):
    class Meta:
        db_table = 'chat_messages'
        managed = False
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чатов'

    id = models.AutoField(primary_key=True)
    ride_id = models.IntegerField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    sender_id = models.IntegerField(null=True, blank=True)
    receiver_id = models.IntegerField(null=True, blank=True)
    message_type = models.CharField(max_length=50, null=True, blank=True)
    attachments = models.JSONField(null=True, blank=True)
    is_moderated = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Message {self.id}"  
