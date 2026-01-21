from django.db import models


class PhoneVerification(models.Model):
    class Meta:
        db_table = 'phone_verifications'
        managed = False
        verbose_name = 'Подтверждение телефона'
        verbose_name_plural = 'Подтверждения телефона'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    attempts = models.IntegerField()
    is_registred = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.phone}"
