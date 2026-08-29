from django.db import models


class AdminPushNotification(models.Model):
    class Meta:
        db_table = "admin_push_notifications"
        managed = False
        verbose_name = "История push-уведомления"
        verbose_name_plural = "История push-уведомлений"

    AUDIENCE_CHOICES = (("user", "Один пользователь"), ("all", "Все аккаунты"))
    STATUS_CHOICES = (
        ("processing", "В процессе"),
        ("sent", "Отправлено"),
        ("partial", "Частично"),
        ("failed", "Ошибка"),
        ("unknown", "Результат неизвестен"),
    )

    id = models.BigAutoField(primary_key=True)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    target_user_id = models.BigIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    operator_id = models.BigIntegerField()
    operator_name = models.CharField(max_length=150)
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    recipient_user_count = models.IntegerField(default=0)
    attempted_token_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id}: {self.title}"
