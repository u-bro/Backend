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
    list_editable = tuple([f for f in list_display if f != 'id' and f not in ['pickup_address', 'pickup_lat', 'pickup_lng', 'dropoff_address', 'dropoff_lat', 'dropoff_lng', 'expected_fare', 'actual_fare', 'distance_meters', 'duration_seconds', 'status', 'cancellation_reason']])
    list_filter = ("status", "is_anomaly", "created_at")
    search_fields = ("pickup_address", "dropoff_address")
    actions = ["cancel_rides", "mark_anomaly_resolved"]

    list_per_page = 25


    readonly_fields = ('id', 'created_at', 'updated_at', 'started_at', 'completed_at', 'canceled_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status in ['completed', 'canceled']:
            readonly.extend(['pickup_address', 'pickup_lat', 'pickup_lng', 'dropoff_address', 'dropoff_lat', 'dropoff_lng', 'expected_fare', 'actual_fare', 'distance_meters', 'duration_seconds', 'status', 'cancellation_reason'])
        return readonly

    def has_add_permission(self, request): 
        return False

    def has_change_permission(self, request, obj=None):  
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):  
        return request.user.groups.filter(name='Admin').exists()

    def ride_actions(self, obj=None):
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

    def cancel_rides(self, request, queryset):  
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

    def mark_anomaly_resolved(self, request, queryset):  
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
