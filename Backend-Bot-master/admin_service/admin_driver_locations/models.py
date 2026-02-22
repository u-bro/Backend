from django.db import models


class DriverLocation(models.Model):
    class Meta:
        db_table = 'driver_locations'
        managed = False
        verbose_name = 'Локация водителя'
        verbose_name_plural = 'Локации водителей'

    id = models.AutoField(primary_key=True)
    driver_profile_id = models.IntegerField()
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=50)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Location {self.id}"
