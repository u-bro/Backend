from django.db import models


class Role(models.Model):
    class Meta:
        db_table = 'roles'
        managed = False
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    code = models.CharField(verbose_name="Код", max_length=50, unique=True)
    name = models.CharField(verbose_name="Название", max_length=100, null=True, blank=True)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    def __str__(self) -> str: 
        return self.name or self.code
