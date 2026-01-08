from django.db import models


class Transaction(models.Model):
    class Meta:
        db_table = 'transactions'
        managed = False
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    is_withdraw = models.BooleanField(default=True)
    amount = models.FloatField()
    created_at = models.DateTimeField()

    def __str__(self) -> str:  
        return f"Transaction {self.id}"
