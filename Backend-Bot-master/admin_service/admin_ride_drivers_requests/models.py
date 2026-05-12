from django.db import models
from utils.schema_choices import RIDE_DRIVERS_REQUEST_STATUS_CHOICES


class RideDriversRequest(models.Model):
    class Meta:
        db_table = 'ride_drivers_requests'
        managed = False
        verbose_name = 'Запрос водителя'
        verbose_name_plural = 'Запросы водителей'

    id = models.AutoField(primary_key=True)
    ride_id = models.IntegerField(null=True, blank=True)
    driver_profile_id = models.IntegerField()
    car_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=RIDE_DRIVERS_REQUEST_STATUS_CHOICES)
    offer_fare = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    eta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Request {self.id}"
