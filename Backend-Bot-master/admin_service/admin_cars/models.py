from django.db import models


class Car(models.Model):
    class Meta:
        db_table = 'cars'
        managed = False
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'

    id = models.AutoField(primary_key=True)
    driver_profile_id = models.IntegerField()
    model = models.CharField(max_length=100, null=True, blank=True)
    number = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=20, null=True, blank=True)
    vin = models.CharField(max_length=100, null=True, blank=True)
    year = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.number or f"Car {self.id}"
