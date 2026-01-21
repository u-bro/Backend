from django.db import models


class InAppNotification(models.Model):
    class Meta:
        db_table = 'in_app_notifications'
        managed = False
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    type = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dedup_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.user_id})"
