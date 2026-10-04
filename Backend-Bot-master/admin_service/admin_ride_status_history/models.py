from django.db import models
from utils.schema_choices import RIDE_STATUS_CHOICES, ROLE_CODE_CHOICES


class RideStatusHistory(models.Model):
    class Meta:
        db_table = 'ride_status_history'
        managed = False
        verbose_name = 'История статуса поездки'
        verbose_name_plural = 'Истории статусов поездок'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    ride_id = models.IntegerField(verbose_name="Номер поездки", null=True, blank=True)
    from_status = models.CharField(verbose_name="Предыдущий статус", max_length=50, null=True, blank=True, choices=RIDE_STATUS_CHOICES)
    to_status = models.CharField(verbose_name="Новый статус", max_length=50, null=True, blank=True, choices=RIDE_STATUS_CHOICES)
    changed_by = models.IntegerField(verbose_name="Кем изменено", null=True, blank=True)
    actor_role = models.CharField(verbose_name="Роль сотрудника", max_length=50, null=True, blank=True, choices=ROLE_CODE_CHOICES)
    reason = models.CharField(verbose_name="Причина", max_length=255, null=True, blank=True)
    meta = models.JSONField(verbose_name="Дополнительные данные", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)

    def __str__(self) -> str:  
        return f"Изменение статуса поездки №{self.ride_id}"
