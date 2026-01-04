from django.db import models


class AdminAuditLog(models.Model):
    class Meta:
        db_table = 'admin_audit_logs'
        managed = False
        verbose_name = 'Лог действий админа'
        verbose_name_plural = 'Логи действий админов'

    id = models.AutoField(primary_key=True)
    admin_user_id = models.IntegerField()
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=50)  # user, driver, tariff, etc.
    target_id = models.IntegerField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # type: ignore[override]
        return f"{self.action} on {self.target_type} {self.target_id} by admin {self.admin_user_id}"
