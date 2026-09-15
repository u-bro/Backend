"""Django groups are staff access roles, separate from mobile-app roles."""
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User

from utils.admin_permissions import all_service_permissions


class AccessRoleForm(forms.ModelForm):
    grant_all_service_permissions = forms.BooleanField(
        required=False,
        label="Выдать все права сервиса",
        help_text=(
            "Заменяет выбранные права всеми правами сервиса, включая модерацию, "
            "поддержку, push и политики. Администраторы доступны только для просмотра. "
            "Управление администраторами и ролями остаётся у суперпользователя."
        ),
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")


class SuperuserWriteMixin:
    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser


class AccessRoleAdmin(SuperuserWriteMixin, GroupAdmin):
    form = AccessRoleForm
    fields = ("name", "grant_all_service_permissions", "permissions")

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if form.cleaned_data.get("grant_all_service_permissions"):
            form.instance.permissions.set(all_service_permissions())


class AdministratorAdmin(SuperuserWriteMixin, UserAdmin):
    """Also protects direct edit/password URLs and crafted POST requests."""


admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(Group, AccessRoleAdmin)
admin.site.register(User, AdministratorAdmin)
