from django.db import models
from utils.schema_choices import DRIVER_DOCUMENT_STATUS_CHOICES, DRIVER_DOCUMENT_TYPE_CHOICES


class DriverDocument(models.Model):
    class Meta:
        db_table = 'driver_documents'
        managed = False
        verbose_name = 'Документ водителя'
        verbose_name_plural = 'Документы водителей'

    id = models.AutoField(verbose_name="Номер записи", primary_key=True)
    driver_profile_id = models.IntegerField(verbose_name="Номер профиля водителя")
    doc_type = models.CharField(verbose_name="Тип документа", max_length=50, choices=DRIVER_DOCUMENT_TYPE_CHOICES)
    file_bucket_key = models.CharField(verbose_name="Ключ файла в хранилище", max_length=2048)
    status = models.CharField(verbose_name="Статус", max_length=50, null=True, blank=True, choices=DRIVER_DOCUMENT_STATUS_CHOICES)
    reviewed_by = models.IntegerField(verbose_name="Кем проверено", null=True, blank=True)
    reviewed_at = models.DateTimeField(verbose_name="Дата проверки", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", null=True, blank=True)

    def __str__(self) -> str:  
        return f"{self.get_doc_type_display()} — водитель №{self.driver_profile_id}"
