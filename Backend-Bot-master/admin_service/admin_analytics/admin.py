from django.contrib import admin
from django.contrib import messages
from utils.api_client import api_client
from utils.audit import AuditLogger

from .models import RideAnomaly


@admin.register(RideAnomaly)
class RideAnomalyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id",
        "expected_fare",
        "actual_fare",
        "difference",
        "difference_percentage",
        "anomaly_type",
        "severity",
        "is_reviewed",
        "created_at",
    )
    list_editable = tuple([f for f in list_display if f != 'id' and f not in ['expected_fare', 'actual_fare', 'difference', 'difference_percentage', 'anomaly_type', 'severity', 'notes']])
    list_filter = ("anomaly_type", "severity", "is_reviewed", "created_at")
    search_fields = ("notes",)
    actions = ["mark_as_reviewed", "assign_to_me"]

    readonly_fields = ('id', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_reviewed:
            readonly.extend(['expected_fare', 'actual_fare', 'difference', 'difference_percentage', 'anomaly_type', 'severity', 'notes'])
        return readonly

    def has_add_permission(self, request): 
        return True

    def has_change_permission(self, request, obj=None):  
        return True 
    def has_delete_permission(self, request, obj=None):  
        return True

    def mark_as_reviewed(self, request, queryset):  
        """Mark anomalies as reviewed"""
        count = 0
        for anomaly in queryset:
            if api_client.review_anomaly(anomaly.id, request.user.id):
                count += 1
                AuditLogger.log_anomaly_review(request.user.id, anomaly.id)
        self.message_user(request, f"Marked {count} anomalies as reviewed", messages.SUCCESS)

    def assign_to_me(self, request, queryset):  
        """Assign anomalies to current admin"""
        count = 0
        for anomaly in queryset:
            if api_client.review_anomaly(anomaly.id, request.user.id):
                count += 1
                AuditLogger.log_anomaly_review(request.user.id, anomaly.id)
        self.message_user(request, f"Assigned {count} anomalies to you", messages.SUCCESS)
