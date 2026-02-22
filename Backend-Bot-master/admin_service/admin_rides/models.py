from django.db import models


class Ride(models.Model):
    class Meta:
        db_table = 'rides'
        managed = False
        verbose_name = 'Поездка'
        verbose_name_plural = 'Поездки'

    id = models.AutoField(primary_key=True)
    client_id = models.IntegerField()
    driver_profile_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    status_reason = models.CharField(max_length=255, null=True, blank=True)
    pickup_address = models.CharField(max_length=500, null=True, blank=True)
    pickup_lat = models.DecimalField(max_digits=12, decimal_places=8)
    pickup_lng = models.DecimalField(max_digits=12, decimal_places=8)
    dropoff_address = models.CharField(max_length=500, null=True, blank=True)
    dropoff_lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    dropoff_lng = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, null=True, blank=True)
    expected_fare = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_fare_snapshot = models.JSONField(null=True, blank=True)
    driver_fare = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    actual_fare = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    distance_meters = models.IntegerField(null=True, blank=True)
    distance_str = models.CharField(max_length=50, null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    duration_str = models.CharField(max_length=50, null=True, blank=True)
    commission_id = models.IntegerField(null=True, blank=True)
    is_anomaly = models.BooleanField(default=False)
    anomaly_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    tariff_plan_id = models.IntegerField()
    ride_class = models.TextField()
    comment = models.TextField(null=True, blank=True)
    ride_type = models.TextField()

    def __str__(self) -> str:  
        return f"Ride {self.id}"
