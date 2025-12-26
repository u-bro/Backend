from django.db import models


class DriverRating(models.Model):
    class Meta:
        db_table = 'driver_ratings'
        managed = False
        verbose_name = 'Рейтинг водителя'
        verbose_name_plural = 'Рейтинги водителей'

    id = models.AutoField(primary_key=True)
    driver_profile_id = models.IntegerField()
    client_id = models.IntegerField()
    ride_id = models.IntegerField()
    rate = models.IntegerField()
    comment = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # type: ignore[override]
        return f"Rating {self.rate} for driver {self.driver_profile_id}"
