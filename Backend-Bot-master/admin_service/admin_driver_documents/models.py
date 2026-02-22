from django.db import models


class DriverDocument(models.Model):
    class Meta:
        db_table = 'driver_documents'
        managed = False
        verbose_name = 'Документ водителя'
        verbose_name_plural = 'Документы водителей'

    id = models.AutoField(primary_key=True)
    driver_profile_id = models.IntegerField()
    doc_type = models.CharField(max_length=50)
    file_url = models.CharField(max_length=2048)
    status = models.CharField(max_length=50, null=True, blank=True)
    reviewed_by = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  
        return f"{self.doc_type} for driver {self.driver_profile_id}"
