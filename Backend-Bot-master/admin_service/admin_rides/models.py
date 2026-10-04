from django.db import models
from utils.schema_choices import RIDE_CLASS_CHOICES, RIDE_STATUS_CHOICES, RIDE_TYPE_CHOICES


class Ride(models.Model):
    class Meta:
        db_table = 'rides'
        managed = False
        verbose_name = 'Поездка'
        verbose_name_plural = 'Поездки'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    client_id = models.IntegerField(verbose_name="Номер клиента")
    driver_profile_id = models.IntegerField(verbose_name="Номер профиля водителя", null=True, blank=True)
    status = models.CharField(verbose_name="Статус", max_length=50, null=True, blank=True, choices=RIDE_STATUS_CHOICES)
    status_reason = models.CharField(verbose_name="Причина изменения статуса", max_length=255, null=True, blank=True)
    pickup_address = models.CharField(verbose_name="Адрес подачи", max_length=500, null=True, blank=True)
    pickup_lat = models.DecimalField(verbose_name="Широта точки подачи", max_digits=12, decimal_places=8)
    pickup_lng = models.DecimalField(verbose_name="Долгота точки подачи", max_digits=12, decimal_places=8)
    dropoff_address = models.CharField(verbose_name="Адрес назначения", max_length=500, null=True, blank=True)
    dropoff_lat = models.DecimalField(verbose_name="Широта точки назначения", max_digits=12, decimal_places=8, null=True, blank=True)
    dropoff_lng = models.DecimalField(verbose_name="Долгота точки назначения", max_digits=12, decimal_places=8, null=True, blank=True)
    scheduled_at = models.DateTimeField(verbose_name="Запланированное время", null=True, blank=True)
    started_at = models.DateTimeField(verbose_name="Дата начала", null=True, blank=True)
    completed_at = models.DateTimeField(verbose_name="Дата завершения", null=True, blank=True)
    canceled_at = models.DateTimeField(verbose_name="Дата отмены", null=True, blank=True)
    cancellation_reason = models.CharField(verbose_name="Причина отмены", max_length=255, null=True, blank=True)
    expected_fare = models.DecimalField(verbose_name="Расчётная стоимость", max_digits=15, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(verbose_name="Сумма комиссии", max_digits=15, decimal_places=2, null=True, blank=True)
    actual_fare = models.DecimalField(verbose_name="Итоговая стоимость", max_digits=15, decimal_places=2, null=True, blank=True)
    distance_meters = models.IntegerField(verbose_name="Расстояние в метрах", null=True, blank=True)
    distance_str = models.CharField(verbose_name="Расстояние", max_length=50, null=True, blank=True)
    duration_seconds = models.IntegerField(verbose_name="Длительность в секундах", null=True, blank=True)
    duration_str = models.CharField(verbose_name="Длительность", max_length=50, null=True, blank=True)
    commission_id = models.IntegerField(verbose_name="Номер комиссии", null=True, blank=True)
    is_anomaly = models.BooleanField(verbose_name="Есть отклонение", default=False)
    anomaly_reason = models.TextField(verbose_name="Причина отклонения", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)
    ride_class = models.TextField(verbose_name="Класс поездки", choices=RIDE_CLASS_CHOICES)
    comment = models.TextField(verbose_name="Комментарий", null=True, blank=True)
    ride_type = models.TextField(verbose_name="Тип поездки", choices=RIDE_TYPE_CHOICES)

    def __str__(self) -> str:  
        return f"Поездка №{self.id}"
