from django.contrib import admin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
import re
from utils.api_client import api_client
from utils.admin_links import safe_external_url

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    change_form_template = "admin/admin_users/user/change_form.html"
    list_display = (
        "id",
        "phone",
        "first_name",
        "last_name",
        "is_active",
        "status",
        "role_id",
        "created_at",
        "last_active_at",
    )
    list_editable = tuple([
        f for f in list_display if f != 'id' and any(f == fld.name for fld in User._meta.fields) and f != 'phone'
    ])

    list_per_page = 25

    readonly_fields = ('id', 'created_at', 'last_active_at', 'photo_preview')
    fieldsets = (
        ("Профиль", {"fields": ("photo_preview", "photo_url", "first_name", "last_name", "middle_name")}),
        ("Контакты", {"fields": ("phone", "email", "city")}),
        ("Статус и роль", {"fields": ("is_active", "status", "role_id")}),
        ("Служебная информация", {"fields": ("id", "created_at", "updated_at", "last_active_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Изображение пользователя")
    def photo_preview(self, obj):
        photo_url = safe_external_url(getattr(obj, "photo_url", None))
        if not photo_url:
            return "Изображение не загружено."
        return format_html(
            '<a class="user-avatar-link" href="{}" target="_blank" rel="noopener">'
            '<img class="user-avatar" src="{}" alt="Изображение пользователя"></a>',
            photo_url,
            photo_url,
        )

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
    list_filter = ("is_active", "status", "role_id")
    search_fields = ("phone", "first_name", "last_name")
    actions = ["block_users", "unblock_users"]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        normalized_phone = re.sub(r"\D", "", search_term or "")
        if normalized_phone:
            queryset = queryset | self.model.objects.filter(
                Q(phone__icontains=search_term) | Q(phone__iregex=rf"[^0-9]*{'[^0-9]*'.join(normalized_phone)}[^0-9]*")
            )

        return queryset.distinct(), use_distinct

    def delete_queryset(self, request, queryset):
        pks = list(queryset.values_list("pk", flat=True))
        self.model.objects.filter(pk__in=pks).delete()

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
            user.is_active = False
            user.save()
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
