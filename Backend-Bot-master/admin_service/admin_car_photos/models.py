from django.db import models
from utils.schema_choices import CAR_PHOTO_STATUS_CHOICES


class CarPhoto(models.Model):
    class Meta:
        db_table = 'car_photos'
        managed = False
        verbose_name = 'Фото автомобиля'
        verbose_name_plural = 'Фото автомобилей'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    car_id = models.IntegerField(verbose_name="Номер автомобиля в системе")
    type = models.CharField(verbose_name="Тип", max_length=50, null=True, blank=True)
    description = models.CharField(verbose_name="Описание", max_length=255, null=True, blank=True)
    photo_url = models.CharField(verbose_name="Ссылка на фотографию", max_length=2048, null=True, blank=True)
    status = models.CharField(verbose_name="Статус", max_length=50, null=True, blank=True, choices=CAR_PHOTO_STATUS_CHOICES)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    def __str__(self) -> str:
        return f"Фотография автомобиля №{self.id}"
