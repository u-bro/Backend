from django.db import models


class TariffPlan(models.Model):
    class Meta:
        db_table = 'tariff_plans'
        managed = False
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)

    base_fare = models.FloatField()
    rate_per_meter = models.FloatField()
    multiplier = models.FloatField()
    rules = models.JSONField(null=True, blank=True)
    commission_percentage = models.FloatField()

    def __str__(self) -> str:  
        return self.name or f"Tariff {self.id}"
