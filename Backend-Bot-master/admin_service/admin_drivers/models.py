from utils.moderation_labels import REASON_LABELS
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from utils.schema_choices import DRIVER_PROFILE_STATUS_CHOICES, RIDE_CLASS_CHOICES


def default_classes_allowed():
    return ["light"]


class DriverModerationInfo(models.Model):
    class Meta:
        db_table = 'driver_moderation_info'
        managed = False
        verbose_name = 'Причина модерации'
        verbose_name_plural = 'Причины модерации'

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    code = models.CharField(verbose_name="Код", max_length=50)
    message = models.CharField(verbose_name="Сообщение", max_length=255)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)

    def __str__(self) -> str:
        code = getattr(self, "code", "") or ""
        message = getattr(self, "message", "") or ""
        return REASON_LABELS.get(code, message or "Причина не указана")


class DriverProfile(models.Model):
    STATUS_WAITING_REGISTER = "waiting_register"
    STATUS_WAITING_APPROVED = "waiting_approved"
    STATUS_WAITING_MODERATION = "waiting_moderation"
    STATUS_APPROVED = "approved"

    STATUS_CHOICES = DRIVER_PROFILE_STATUS_CHOICES

    class Meta:
        db_table = 'driver_profiles'
        managed = False
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    user_id = models.BigIntegerField(verbose_name="Номер пользователя")
    first_name = models.CharField(verbose_name="Имя", max_length=100, null=True, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=100, null=True, blank=True)
    middle_name = models.CharField(verbose_name="Отчество", max_length=100, null=True, blank=True)
    birth_date = models.DateTimeField(verbose_name="Дата рождения", null=True, blank=True)
    photo_url = models.CharField(verbose_name="Ссылка на фотографию", max_length=2048, null=True, blank=True)
    license_number = models.CharField(verbose_name="Номер водительского удостоверения", max_length=100, null=True, blank=True)
    license_category = models.CharField(verbose_name="Категории водительского удостоверения", max_length=20, null=True, blank=True)
    license_issued_at = models.DateTimeField(verbose_name="Дата выдачи водительского удостоверения", null=True, blank=True)
    license_expires_at = models.DateTimeField(verbose_name="Срок действия водительского удостоверения", null=True, blank=True)
    experience_years = models.IntegerField(verbose_name="Стаж вождения в годах", null=True, blank=True)
    approved = models.BooleanField(verbose_name="Одобрен", default=False)
    approved_by = models.BigIntegerField(verbose_name="Кем одобрен", null=True, blank=True)
    approved_at = models.DateTimeField(verbose_name="Дата одобрения", null=True, blank=True)
    status = models.CharField(verbose_name="Статус", max_length=50, choices=STATUS_CHOICES)
    classes_allowed = models.JSONField(verbose_name="Разрешённые классы", null=False, blank=False, default=default_classes_allowed)
    current_class = models.CharField(verbose_name="Текущий класс", max_length=50, null=True, blank=True, choices=RIDE_CLASS_CHOICES)
    current_car_id = models.BigIntegerField(verbose_name="Текущий автомобиль", null=True, blank=True)
    rating_avg = models.DecimalField(verbose_name="Средний рейтинг", max_digits=3, decimal_places=2, null=True, blank=True, default=settings.DRIVER_PROFILE_INITIAL_RATING_AVG, validators=[MinValueValidator(0)])
    rating_count = models.IntegerField(verbose_name="Количество оценок", null=True, blank=True, default=settings.DRIVER_PROFILE_INITIAL_RATING_COUNT, validators=[MinValueValidator(0)])
    ride_count = models.IntegerField(verbose_name="Количество поездок", null=True, blank=True, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    moderation_info = models.ManyToManyField(
        DriverModerationInfo,
        through="DriverProfileModeration",
        related_name="driver_profiles",
        blank=True,
        verbose_name="Замечания к профилю",
    )

    def __str__(self) -> str: 
        name_parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(name_parts) or f"Водитель {self.id}"


class DriverProfileModeration(models.Model):
    class Meta:
        db_table = 'driver_profile_moderation'
        managed = False
        verbose_name = 'Модерация профиля водителя'
        verbose_name_plural = 'Модерации профилей водителей'

    id = models.BigAutoField(verbose_name="Номер записи", primary_key=True)
    driver_profile = models.ForeignKey(
        DriverProfile,
        on_delete=models.DO_NOTHING,
        db_column='driver_profile_id',
        related_name='moderations',
        verbose_name="Профиль водителя",
    )
    driver_moderation_info = models.ForeignKey(
        DriverModerationInfo,
        on_delete=models.DO_NOTHING,
        db_column='driver_moderation_info_id',
        related_name='moderations',
        verbose_name="Замечание к профилю",
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)

    def __str__(self) -> str:
        return str(getattr(self, "driver_moderation_info", ""))
