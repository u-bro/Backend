from django.db import models


class CommissionPayment(models.Model):
    class Meta:
        db_table = 'commission_payments'
        managed = False
        verbose_name = 'Платеж комиссии'
        verbose_name_plural = 'Платежи комиссий'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)

    ride_id = models.IntegerField(verbose_name="Номер поездки", null=True, blank=True)
    user_id = models.IntegerField(verbose_name="Номер пользователя")

    amount = models.DecimalField(verbose_name="Сумма", max_digits=15, decimal_places=2)
    currency = models.CharField(verbose_name="Валюта", max_length=10)

    status = models.CharField(verbose_name="Статус", max_length=32)
    payment_link = models.CharField(verbose_name="Ссылка на оплату", max_length=2048, null=True, blank=True)

    purpose = models.CharField(verbose_name="Назначение", max_length=255, null=True, blank=True)

    paid_at = models.DateTimeField(verbose_name="Дата оплаты", null=True, blank=True)
    payment_id = models.CharField(verbose_name="Номер платежа", max_length=128, null=True, blank=True)

    is_refund = models.BooleanField(verbose_name="Возврат", default=False)

    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name="Дата изменения", null=True, blank=True)

    def __str__(self) -> str:
        return f"Оплата комиссии №{self.id}"
