from django.db import models


class RideAnomaly(models.Model):
    class Meta:
        db_table = 'ride_anomalies'
        managed = False
        verbose_name = 'Аномалия поездки'
        verbose_name_plural = 'Аномалии поездок'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    ride_id = models.IntegerField(verbose_name="Номер поездки")
    expected_fare = models.DecimalField(verbose_name="Расчётная стоимость", max_digits=15, decimal_places=2)
    actual_fare = models.DecimalField(verbose_name="Итоговая стоимость", max_digits=15, decimal_places=2)
    difference = models.DecimalField(verbose_name="Разница", max_digits=15, decimal_places=2)
    difference_percentage = models.DecimalField(verbose_name="Разница в процентах", max_digits=5, decimal_places=2)
    anomaly_type = models.CharField(verbose_name="Тип отклонения", max_length=50)
    severity = models.CharField(verbose_name="Важность", max_length=20)
    is_reviewed = models.BooleanField(verbose_name="Проверено", default=False)
    reviewed_by = models.IntegerField(verbose_name="Кем проверено", null=True, blank=True)
    reviewed_at = models.DateTimeField(verbose_name="Дата проверки", null=True, blank=True)
    notes = models.TextField(verbose_name="Примечания", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def __str__(self) -> str:  
        return f"Отклонение в поездке №{self.ride_id}: {self.difference}"
