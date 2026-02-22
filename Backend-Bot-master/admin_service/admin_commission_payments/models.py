from django.db import models


class CommissionPayment(models.Model):
    class Meta:
        db_table = 'commission_payments'
        managed = False
        verbose_name = 'Платеж комиссии'
        verbose_name_plural = 'Платежи комиссий'

    id = models.AutoField(primary_key=True)

    ride_id = models.IntegerField()
    user_id = models.IntegerField()

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10)

    status = models.CharField(max_length=32)

    tochka_operation_id = models.CharField(max_length=64, null=True, blank=True)
    payment_link = models.CharField(max_length=2048, null=True, blank=True)

    purpose = models.CharField(max_length=255, null=True, blank=True)
    payment_mode = models.JSONField(null=True, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    payment_id = models.CharField(max_length=128, null=True, blank=True)

    is_refund = models.BooleanField(default=False)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"CommissionPayment {self.id}"
