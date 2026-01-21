from django.db import models


class DeviceToken(models.Model):
    class Meta:
        db_table = 'device_tokens'
        managed = False
        verbose_name = 'Токен устройства'
        verbose_name_plural = 'Токены устройств'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    token = models.CharField(max_length=255)
    platform = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.platform} {self.user_id}"
