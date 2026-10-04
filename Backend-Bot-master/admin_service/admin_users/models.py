from django.db import models
from utils.schema_choices import USER_STATUS_CHOICES


class User(models.Model):
    class Meta:
        db_table = 'users'
        managed = False
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)
    last_active_at = models.DateTimeField(verbose_name="Последняя активность", null=True, blank=True)
    first_name = models.CharField(verbose_name="Имя", max_length=100, null=True, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=100, null=True, blank=True)
    middle_name = models.CharField(verbose_name="Отчество", max_length=100, null=True, blank=True)
    phone = models.CharField(verbose_name="Телефон", max_length=20, unique=True, null=True, blank=True)
    email = models.CharField(verbose_name="Электронная почта", max_length=255, unique=True, null=True, blank=True)
    city = models.CharField(verbose_name="Город", max_length=100, null=True, blank=True)
    photo_url = models.CharField(verbose_name="Ссылка на фотографию", max_length=2048, null=True, blank=True)
    is_active = models.BooleanField(verbose_name="Активен", default=True)
    status = models.CharField(verbose_name="Статус", max_length=50, default="active", choices=USER_STATUS_CHOICES)
    role_id = models.IntegerField(verbose_name="Номер роли")

    def __str__(self) -> str: 
        if self.phone:
            return f"{self.phone}"
        return str(self.id)
