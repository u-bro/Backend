from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import AdminPushNotification


@admin.register(AdminPushNotification)
class AdminPushNotificationAdmin(admin.ModelAdmin):
    change_list_template = "admin/admin_push_notifications/adminpushnotification/change_list.html"
    list_display = (
        "id",
        "created_at",
        "operator_name",
        "audience",
        "target_user_link",
        "title",
        "status",
        "attempted_token_count",
        "success_count",
        "failure_count",
        "duplicate_fingerprint_link",
    )
    list_filter = ("audience", "status", "created_at")
    search_fields = ("title", "body", "operator_name", "target_user_id", "fingerprint")
    readonly_fields = tuple(field.name for field in AdminPushNotification._meta.fields)
    ordering = ("-created_at", "-id")

    @admin.display(description="Пользователь")
    def target_user_link(self, obj):
        if not obj.target_user_id:
            return "Все"
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:admin_users_user_change", args=[obj.target_user_id]),
            obj.target_user_id,
        )

    @admin.display(description="Похожие отправки")
    def duplicate_fingerprint_link(self, obj):
        url = reverse("admin:admin_push_notifications_adminpushnotification_changelist")
        return format_html('<a href="{}?q={}">По fingerprint</a>', url, obj.fingerprint)

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return bool(
            request.user.is_active
            and request.user.is_staff
            and (request.user.is_superuser or request.user.groups.filter(name="Admin").exists())
        )

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
