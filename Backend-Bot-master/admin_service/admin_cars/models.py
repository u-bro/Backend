from django.db import models


class Car(models.Model):
    class Meta:
        db_table = 'cars'
        managed = False
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    driver_profile_id = models.IntegerField(verbose_name="Номер профиля водителя")
    model = models.CharField(verbose_name="Модель", max_length=100, null=True, blank=True)
    number = models.CharField(verbose_name="Госномер", max_length=100, null=True, blank=True)
    region = models.CharField(verbose_name="Регион", max_length=20, null=True, blank=True)
    vin = models.CharField(verbose_name="Идентификационный номер автомобиля (VIN)", max_length=100, null=True, blank=True)
    year = models.CharField(verbose_name="Год выпуска", max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    def __str__(self) -> str:
        return self.number or f"Car {self.id}"
