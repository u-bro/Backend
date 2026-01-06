from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from utils.api_client import api_client

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "phone",
        "first_name",
        "last_name",
        "is_active",
        "role_id",
        "created_at",
        "last_active_at",
    )
    list_editable = tuple([
        f for f in list_display if f != 'id' and any(f == fld.name for fld in User._meta.fields) and f != 'phone'
    ])

    readonly_fields = ('id', 'created_at', 'last_active_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_active:
            readonly.append('phone')
        return readonly

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        actual_fields = [
            f for f in self.list_display if any(f == fld.name for fld in User._meta.fields)
        ]
        if 'id' not in actual_fields:
            actual_fields = ['id'] + actual_fields
        try:
            return qs.only(*actual_fields)
        except Exception:
            return qs
    list_filter = ("is_active", "role_id")
    search_fields = ("phone", "first_name", "last_name")
    actions = ["block_users", "unblock_users"]

    def has_add_permission(self, request):  
        return request.user.groups.filter(name='Admin').exists()

    def has_change_permission(self, request, obj=None): 
        return request.user.groups.filter(name__in=['Admin', 'Operator']).exists()

    def has_delete_permission(self, request, obj=None): 
        return request.user.groups.filter(name='Admin').exists()

    def block_users(self, request, queryset):  

        if not request.user.groups.filter(name__in=['Admin', 'Operator']).exists():
            self.message_user(request, "No permission", messages.ERROR)
            return
            
        count = 0
        for user in queryset:
            print(f"Blocking user {user.id}, current is_active: {user.is_active}")
            user.is_active = False
            user.save()
            print(f"After save, is_active: {user.is_active}")
            count += 1
        self.message_user(request, f"Blocked {count} users", messages.SUCCESS)

    def unblock_users(self, request, queryset):  
        if not request.user.groups.filter(name='Admin').exists():
            self.message_user(request, "Only Admin can unblock users", messages.ERROR)
            return
            
        count = 0
        for user in queryset:
            user.is_active = True
            user.save()
            count += 1
        self.message_user(request, f"Unblocked {count} users", messages.SUCCESS)
