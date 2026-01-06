from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from utils.api_client import api_client

from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "display_name",
        "first_name",
        "last_name",
        "approved",
        "documents_status",
        "user_is_active",
        "rating_avg",
        "created_at",
        "updated_at",
    )
    # Only include real model fields in list_editable (exclude admin methods like `user_is_active`)
    # Compute membership directly to avoid referencing an intermediate name that could be undefined
    list_editable = tuple(
        [f for f in list_display if f != 'id' and any(f == fld.name for fld in DriverProfile._meta.fields) and f not in ['license_number', 'license_category', 'license_issued_at', 'license_expires_at', 'experience_years', 'qualification_level', 'classes_allowed']]
    )
    list_filter = ("approved", "documents_status")
    search_fields = ("display_name", "first_name", "last_name")
    actions = ["approve_drivers", "reject_drivers", "block_drivers", "unblock_drivers"]

    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.approved:
            readonly.extend(['license_number', 'license_category', 'license_issued_at', 'license_expires_at', 'experience_years', 'qualification_level', 'classes_allowed'])
        return readonly

    def has_add_permission(self, request):  # type: ignore[override]
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name='Admin').exists()

    def user_is_active(self, obj):  # type: ignore[override]
        """Show user active status"""
        try:
            from admin_users.models import User
            user = User.objects.filter(id=obj.user_id).first()
            return "Active" if user and user.is_active else "Blocked"
        except:
            return "Unknown"
    user_is_active.short_description = "User Status"

    def approve_drivers(self, request, queryset):  # type: ignore[override]
        """Mass approve drivers"""
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            driver.approved = True
            driver.approved_by = request.user.id
            driver.approved_at = timezone.now()
            driver.save()
            count += 1
        self.message_user(request, f"Approved {count} drivers", messages.SUCCESS)

    def reject_drivers(self, request, queryset):  # type: ignore[override]
        """Mass reject drivers"""
        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            driver.approved = False
            driver.approved_by = request.user.id
            driver.approved_at = timezone.now()
            driver.save()
            count += 1
        self.message_user(request, f"Rejected {count} drivers", messages.SUCCESS)

    def block_drivers(self, request, queryset):  # type: ignore[override]
        """Block drivers"""
        if not request.user.groups.filter(name='Admin').exists():
            self.message_user(request, "Only Admin can block drivers", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            from admin_users.models import User
            user = User.objects.filter(id=driver.user_id).first()
            if user:
                user.is_active = False
                user.save()
                count += 1
        self.message_user(request, f"Blocked {count} drivers", messages.SUCCESS)

    def unblock_drivers(self, request, queryset):  # type: ignore[override]
        """Unblock drivers"""
        if not request.user.groups.filter(name='Admin').exists():
            self.message_user(request, "Only Admin can unblock drivers", messages.ERROR)
            return
            
        count = 0
        for driver in queryset:
            from admin_users.models import User
            user = User.objects.filter(id=driver.user_id).first()
            if user:
                user.is_active = True
                user.save()
                count += 1
        self.message_user(request, f"Unblocked {count} drivers", messages.SUCCESS)
