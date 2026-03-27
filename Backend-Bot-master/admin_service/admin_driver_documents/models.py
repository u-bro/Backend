from django.db import models
from utils.schema_choices import DRIVER_DOCUMENT_STATUS_CHOICES, DRIVER_DOCUMENT_TYPE_CHOICES


class DriverDocument(models.Model):
    class Meta:
        db_table = 'driver_documents'
        managed = False
        verbose_name = 'Документ водителя'
        verbose_name_plural = 'Документы водителей'

    id = models.AutoField(primary_key=True)
    driver_profile_id = models.IntegerField()
    doc_type = models.CharField(max_length=50, choices=DRIVER_DOCUMENT_TYPE_CHOICES)
    file_bucket_key = models.CharField(max_length=2048)
    status = models.CharField(max_length=50, null=True, blank=True, choices=DRIVER_DOCUMENT_STATUS_CHOICES)
    reviewed_by = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  
        return f"{self.doc_type} for driver {self.driver_profile_id}"
