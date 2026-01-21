from django.db import models


class RefreshToken(models.Model):
    class Meta:
        db_table = 'refresh_tokens'
        managed = False
        verbose_name = 'Refresh токен'
        verbose_name_plural = 'Refresh токены'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    token = models.CharField(max_length=255)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Token {self.id}"
