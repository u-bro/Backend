from django.db import models
from utils.schema_choices import RIDE_DRIVERS_REQUEST_STATUS_CHOICES, RIDE_REQUEST_REMOVAL_REASON_CHOICES


class RideDriversRequest(models.Model):
    class Meta:
        db_table = 'ride_drivers_requests'
        managed = False
        verbose_name = 'Запрос водителя'
        verbose_name_plural = 'Запросы водителей'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    ride_id = models.IntegerField(verbose_name="Номер поездки", null=True, blank=True)
    driver_profile_id = models.IntegerField(verbose_name="Номер профиля водителя")
    car_id = models.IntegerField(verbose_name="Номер автомобиля в системе", null=True, blank=True)
    status = models.CharField(verbose_name="Статус", max_length=50, choices=RIDE_DRIVERS_REQUEST_STATUS_CHOICES)
    offer_fare = models.DecimalField(verbose_name="Предложенная стоимость", max_digits=15, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(verbose_name="Сумма комиссии", max_digits=15, decimal_places=2, null=True, blank=True)
    removal_reason = models.CharField(verbose_name="Причина удаления", max_length=50, choices=RIDE_REQUEST_REMOVAL_REASON_CHOICES, null=True, blank=True)
    eta = models.JSONField(verbose_name="Расчётное время прибытия", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    def __str__(self) -> str:
        return f"Отклик №{self.id}"
