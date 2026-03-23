from django.db import models
from django.core.validators import MinValueValidator


class DriverModerationInfo(models.Model):
    class Meta:
        db_table = 'driver_moderation_info'
        managed = False
        verbose_name = 'Причина модерации'
        verbose_name_plural = 'Причины модерации'

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        code = getattr(self, "code", "") or ""
        message = getattr(self, "message", "") or ""
        return f"{code}: {message}".strip(": ")


class DriverProfile(models.Model):
    STATUS_WAITING_REGISTER = "waiting_register"
    STATUS_WAITING_APPROVED = "waiting_approved"
    STATUS_WAITING_MODERATION = "waiting_moderation"
    STATUS_APPROVED = "approved"

    STATUS_CHOICES = (
        (STATUS_WAITING_REGISTER, "waiting_register"),
        (STATUS_WAITING_APPROVED, "waiting_approved"),
        (STATUS_WAITING_MODERATION, "waiting_moderation"),
        (STATUS_APPROVED, "approved"),
    )

    class Meta:
        db_table = 'driver_profiles'
        managed = False
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'

    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateTimeField(null=True, blank=True)
    photo_url = models.CharField(max_length=2048, null=True, blank=True)
    license_number = models.CharField(max_length=100, null=True, blank=True)
    license_category = models.CharField(max_length=20, null=True, blank=True)
    license_issued_at = models.DateTimeField(null=True, blank=True)
    license_expires_at = models.DateTimeField(null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    classes_allowed = models.JSONField(null=False, blank=False, default=['light'])
    current_class = models.CharField(max_length=50, null=True, blank=True)
    current_car_id = models.BigIntegerField(null=True, blank=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, default=5.0, validators=[MinValueValidator(0)])
    rating_count = models.IntegerField(null=True, blank=True, default=0, validators=[MinValueValidator(0)])
    ride_count = models.IntegerField(null=True, blank=True, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    moderation_info = models.ManyToManyField(
        DriverModerationInfo,
        through="DriverProfileModeration",
        related_name="driver_profiles",
        blank=True,
    )

    def __str__(self) -> str: 
        name_parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(name_parts) or f"Driver {self.id}"


class DriverProfileModeration(models.Model):
    class Meta:
        db_table = 'driver_profile_moderation'
        managed = False
        verbose_name = 'Модерация профиля водителя'
        verbose_name_plural = 'Модерации профилей водителей'

    id = models.BigAutoField(primary_key=True)
    driver_profile = models.ForeignKey(
        DriverProfile,
        on_delete=models.DO_NOTHING,
        db_column='driver_profile_id',
        related_name='moderations',
    )
    driver_moderation_info = models.ForeignKey(
        DriverModerationInfo,
        on_delete=models.DO_NOTHING,
        db_column='driver_moderation_info_id',
        related_name='moderations',
    )
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(getattr(self, "driver_moderation_info", ""))
