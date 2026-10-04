from django.db import models


class AdminAuditLog(models.Model):
    class Meta:
        db_table = 'admin_audit_logs'
        managed = False
        verbose_name = 'Лог действий админа'
        verbose_name_plural = 'Логи действий админов'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    admin_user_id = models.IntegerField(verbose_name="Номер администратора")
    action = models.CharField(verbose_name="Действие", max_length=100)
    target_type = models.CharField(verbose_name="Тип объекта", max_length=50)
    target_id = models.IntegerField(verbose_name="Номер объекта")
    old_values = models.JSONField(verbose_name="Прежние значения", null=True, blank=True)
    new_values = models.JSONField(verbose_name="Новые значения", null=True, blank=True)
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес", null=True, blank=True)
    user_agent = models.TextField(verbose_name="Браузер или приложение", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def __str__(self) -> str:  
        return f"{self.action}: {self.target_type} №{self.target_id}, администратор №{self.admin_user_id}"
