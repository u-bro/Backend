from django.db import models


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
    qualification_level = models.CharField(max_length=50, null=True, blank=True)
    classes_allowed = models.JSONField()
    current_class = models.CharField(max_length=50, null=True, blank=True)
    documents_status = models.CharField(max_length=50, null=True, blank=True)
    documents_review_notes = models.TextField(null=True, blank=True)
    rating_avg = models.IntegerField(null=True, blank=True)
    rating_count = models.IntegerField(null=True, blank=True)
    ride_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str: 
        name_parts = [self.last_name, self.first_name, self.middle_name]
        name = " ".join([part for part in name_parts if part])
        return name or f"Driver {self.id}"
