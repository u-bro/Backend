from django.db import models


class RideAnomaly(models.Model):
    class Meta:
        db_table = 'ride_anomalies'
        managed = False
        verbose_name = 'Аномалия поездки'
        verbose_name_plural = 'Аномалии поездок'

    id = models.AutoField(primary_key=True)
    ride_id = models.IntegerField()
    expected_fare = models.DecimalField(max_digits=15, decimal_places=2)
    actual_fare = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2)
    difference_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    anomaly_type = models.CharField(max_length=50)  
    severity = models.CharField(max_length=20) 
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  
        return f"Anomaly in ride {self.ride_id}: {self.difference}"
