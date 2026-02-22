from django.db import models


class CarPhoto(models.Model):
    class Meta:
        db_table = 'car_photos'
        managed = False
        verbose_name = 'Фото автомобиля'
        verbose_name_plural = 'Фото автомобилей'

    id = models.AutoField(primary_key=True)
    car_id = models.IntegerField()
    type = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    photo_url = models.CharField(max_length=2048, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"CarPhoto {self.id}"
