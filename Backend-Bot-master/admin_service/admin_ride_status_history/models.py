from django.db import models


class RideStatusHistory(models.Model):
    class Meta:
        db_table = 'ride_status_history'
        managed = False
        verbose_name = 'История статуса поездки'
        verbose_name_plural = 'Истории статусов поездок'

    id = models.AutoField(primary_key=True)
    ride_id = models.IntegerField()
    from_status = models.CharField(max_length=50, null=True, blank=True)
    to_status = models.CharField(max_length=50, null=True, blank=True)
    changed_by = models.IntegerField(null=True, blank=True)
    actor_role = models.CharField(max_length=50, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # type: ignore[override]
        return f"Status change for ride {self.ride_id}"
