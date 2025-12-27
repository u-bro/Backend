from django.contrib import admin
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from utils.api_client import api_client

from .models import Ride


class RideActionForm(forms.Form):
    action_type = forms.ChoiceField(choices=[
        ('cancel', 'Cancel ride'),
        ('assign', 'Assign driver'),
        ('complete', 'Mark as completed')
    ])
    reason = forms.CharField(required=False, widget=forms.Textarea)
    driver_id = forms.IntegerField(required=False, help_text="For assign action")


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_id",
        "driver_profile_id",
        "status",
        "pickup_address",
        "dropoff_address",
        "expected_fare",
        "actual_fare",
        "is_anomaly",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "is_anomaly", "created_at")
    search_fields = ("pickup_address", "dropoff_address")
    actions = ["cancel_rides", "mark_anomaly_resolved"]
    readonly_fields = ("created_at", "updated_at", "ride_actions")

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name='Admin').exists()

    def ride_actions(self, obj=None):
        """Custom action buttons for ride management"""
        if not obj:
            return ""
        
        actions = []
        if obj.status in ['pending', 'assigned']:
            actions.append(f'<a href="/admin/admin_rides/ride/{obj.id}/cancel/" class="button">Cancel</a>')
        if obj.status == 'pending':
            actions.append(f'<a href="/admin/admin_rides/ride/{obj.id}/assign/" class="button">Assign Driver</a>')
        if obj.is_anomaly:
            actions.append(f'<a href="/admin/admin_rides/ride/{obj.id}/resolve/" class="button">Resolve Anomaly</a>')
            
        return mark_safe(' | '.join(actions)) if actions else "No actions available"
    ride_actions.short_description = "Actions"

    def cancel_rides(self, request, queryset):  # type: ignore[override]
        """Mass cancel rides"""
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        for ride in queryset:
            ride.status = "canceled"
            ride.cancellation_reason = "Cancelled by admin"
            ride.canceled_at = timezone.now()
            ride.save()
            count += 1
        self.message_user(request, f"Cancelled {count} rides", messages.SUCCESS)

    def mark_anomaly_resolved(self, request, queryset):  # type: ignore[override]
        """Mark ride anomalies as resolved"""
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        for ride in queryset.filter(is_anomaly=True):
            ride.is_anomaly = False
            ride.anomaly_reason = ""
            ride.save()
            count += 1
        self.message_user(request, f"Resolved {count} anomalies", messages.SUCCESS)
