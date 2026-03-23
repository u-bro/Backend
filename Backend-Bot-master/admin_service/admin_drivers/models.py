from django.db import models
from django.core.validators import MinValueValidator

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
    message_error = models.CharField(max_length=255, null=True, blank=True)
    classes_allowed = models.JSONField(null=False, blank=False, default=['light'])
    current_class = models.CharField(max_length=50, null=True, blank=True)
    current_car_id = models.BigIntegerField(null=True, blank=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    rating_count = models.IntegerField(null=True, blank=True, default=0, validators=[MinValueValidator(0)])
    ride_count = models.IntegerField(null=True, blank=True, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str: 
        name_parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(name_parts) or f"Driver {self.id}"
