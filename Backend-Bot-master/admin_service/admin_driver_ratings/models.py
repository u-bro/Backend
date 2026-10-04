from django.db import models


class DriverRating(models.Model):
    class Meta:
        db_table = 'driver_ratings'
        managed = False
        verbose_name = 'Рейтинг водителя'
        verbose_name_plural = 'Рейтинги водителей'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    driver_profile_id = models.IntegerField(verbose_name="Номер профиля водителя")
    client_id = models.IntegerField(verbose_name="Номер клиента")
    ride_id = models.IntegerField(verbose_name="Номер поездки", null=True, blank=True)
    rate = models.IntegerField(verbose_name="Оценка")
    comment = models.CharField(verbose_name="Комментарий", max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)

    def __str__(self) -> str:  
        return f"Оценка {self.rate} водителю №{self.driver_profile_id}"
