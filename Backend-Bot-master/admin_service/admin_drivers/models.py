from django.db import models
from django.core.validators import MinValueValidator

class DriverProfile(models.Model):
    class Meta:
        db_table = 'driver_profiles'
        managed = False
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateTimeField(null=True, blank=True)
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    license_number = models.CharField(max_length=100, null=True, blank=True)
    license_category = models.CharField(max_length=20, null=True, blank=True)
    license_issued_at = models.DateTimeField(null=True, blank=True)
    license_expires_at = models.DateTimeField(null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.IntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    classes_allowed = models.JSONField(null=False, blank=True, default=['light'])
    current_class = models.CharField(max_length=50, null=True, blank=True)
    current_car_id = models.IntegerField(null=True, blank=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, null=False, blank=False, default=5.0, validators=[MinValueValidator(0)])
    rating_count = models.IntegerField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    ride_count = models.IntegerField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str: 
        name_parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(name_parts) or f"Driver {self.id}"
