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

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    audience = models.CharField(verbose_name="Аудитория", max_length=20, choices=AUDIENCE_CHOICES)
    target_user_id = models.BigIntegerField(verbose_name="Номер пользователя-получателя", null=True, blank=True)
    title = models.CharField(verbose_name="Заголовок", max_length=255)
    body = models.TextField(verbose_name="Текст")
    operator_id = models.BigIntegerField(verbose_name="Номер оператора")
    operator_name = models.CharField(verbose_name="Имя оператора", max_length=150)
    fingerprint = models.CharField(verbose_name="Отпечаток", max_length=64)
    status = models.CharField(verbose_name="Статус", max_length=20, choices=STATUS_CHOICES)
    recipient_user_count = models.IntegerField(verbose_name="Количество получателей", default=0)
    attempted_token_count = models.IntegerField(verbose_name="Количество попыток отправки", default=0)
    success_count = models.IntegerField(verbose_name="Количество успешных отправок", default=0)
    failure_count = models.IntegerField(verbose_name="Количество ошибок", default=0)
    error_message = models.TextField(verbose_name="Сообщение об ошибке", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания")
    completed_at = models.DateTimeField(verbose_name="Дата завершения", null=True, blank=True)

    def __str__(self):
        return f"#{self.id}: {self.title}"
