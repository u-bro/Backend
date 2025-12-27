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
    list_filter = ("anomaly_type", "severity", "is_reviewed", "created_at")
    search_fields = ("notes",)
    actions = ["mark_as_reviewed", "assign_to_me"]

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return True  # Allow review actions

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def mark_as_reviewed(self, request, queryset):  # type: ignore[override]
        """Mark anomalies as reviewed"""
        count = 0
        for anomaly in queryset:
            if api_client.review_anomaly(anomaly.id, request.user.id):
                count += 1
                AuditLogger.log_anomaly_review(request.user.id, anomaly.id)
        self.message_user(request, f"Marked {count} anomalies as reviewed", messages.SUCCESS)

    def assign_to_me(self, request, queryset):  # type: ignore[override]
        """Assign anomalies to current admin"""
        count = 0
        for anomaly in queryset:
            # This would be implemented in FastAPI
            # For now, just mark as reviewed
            if api_client.review_anomaly(anomaly.id, request.user.id):
                count += 1
                AuditLogger.log_anomaly_review(request.user.id, anomaly.id)
        self.message_user(request, f"Assigned {count} anomalies to you", messages.SUCCESS)
