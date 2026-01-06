from django.db import models


class Commission(models.Model):
    class Meta:
        db_table = 'commissions'
        managed = False
        verbose_name = 'Комиссия'
        verbose_name_plural = 'Комиссии'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str: 
        return self.name or f"Commission {self.id}"
