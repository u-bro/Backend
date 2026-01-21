from django.db import models


class User(models.Model):
    class Meta:
        db_table = 'users'
        managed = False
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(null=True, blank=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.CharField(max_length=255, unique=True, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    role_id = models.IntegerField()

    def __str__(self) -> str: 
        if self.phone:
            return f"{self.phone}"
        return str(self.id)
