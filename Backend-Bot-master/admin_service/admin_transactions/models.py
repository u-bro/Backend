from django.db import models


class Transaction(models.Model):
    class Meta:
        db_table = 'commission_payments'
        managed = False
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'

    id = models.AutoField(primary_key=True)
    ride_id = models.IntegerField()
    user_id = models.IntegerField()
    amount = models.FloatField()
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=32)
    is_refund = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    def __str__(self) -> str:  
        return f"Transaction {self.id}"
