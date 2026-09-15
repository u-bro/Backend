from django.contrib import admin
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, RequestFactory
from django.urls import reverse

from admin_users.models import User as ServiceUser
from utils.admin_permissions import all_service_permissions, has_service_permission


class StaffRoleAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser("owner", password="Test-only-9q!Long")
        cls.member = User.objects.create_user("manager", password="Test-only-8z!Long", is_staff=True)
        cls.role = Group.objects.create(name="Управляющий")
        cls.role.permissions.set(all_service_permissions())
        cls.member.groups.add(cls.role)

    def request_for(self, user):
        request = RequestFactory().get("/admin/")
        request.user = user
        return request

    def test_service_role_has_service_permissions_but_no_account_writes(self):
        user = User.objects.get(pk=self.member.pk)
        self.assertTrue(user.has_perm("admin_users.change_user"))
        self.assertTrue(user.has_perm("admin_drivers.change_driverprofile"))
        self.assertTrue(user.has_perm("auth.view_user"))
        self.assertTrue(user.has_perm("auth.manage_service_policies"))
        for model in ("user", "group"):
            for action in ("add", "change", "delete"):
                self.assertFalse(user.has_perm(f"auth.{action}_{model}"))
        model_admin = admin.site._registry[ServiceUser]
        self.assertTrue(model_admin.has_change_permission(self.request_for(user)))

    def test_service_workspaces_accept_custom_role(self):
        from admin_drivers.views import _is_moderator
        from admin_support.views import can_access_support, can_change_support
        from admin_push_notifications.views import can_send_push
        from admin_project.policy_views import _has_policy_access
        user = User.objects.get(pk=self.member.pk)
        self.assertTrue(_is_moderator(self.request_for(user)))
        for check in (can_access_support, can_change_support, can_send_push, _has_policy_access):
            self.assertTrue(check(user), check.__name__)

    def test_staff_without_role_cannot_use_service_permission(self):
        user = User.objects.create_user("viewer", is_staff=True)
        self.assertFalse(has_service_permission(user, "admin_users.change_user"))
        self.member.is_active = False
        self.assertFalse(has_service_permission(self.member, "admin_users.change_user"))

    def test_direct_account_and_role_writes_are_denied_even_with_permissions(self):
        self.member.user_permissions.set(Permission.objects.filter(content_type__app_label="auth"))
        self.client.force_login(self.member)
        urls = [
            reverse("admin:auth_user_add"),
            reverse("admin:auth_user_change", args=[self.owner.pk]),
            reverse("admin:auth_user_delete", args=[self.owner.pk]),
            reverse("admin:auth_user_password_change", args=[self.owner.pk]),
            reverse("admin:auth_group_add"),
            reverse("admin:auth_group_change", args=[self.role.pk]),
            reverse("admin:auth_group_delete", args=[self.role.pk]),
        ]
        original_hash = self.owner.password
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {"name": "Escalated", "is_superuser": "on"}).status_code, 403)
        self.owner.refresh_from_db()
        self.role.refresh_from_db()
        self.assertEqual(self.owner.password, original_hash)
        self.assertEqual(self.role.name, "Управляющий")
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 200)

    def test_owner_can_create_edit_and_delete_role_in_admin(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("admin:auth_group_add"), {
            "name": "Новая роль", "grant_all_service_permissions": "on", "_save": "Сохранить",
        })
        self.assertEqual(response.status_code, 302)
        role = Group.objects.get(name="Новая роль")
        self.assertTrue(role.permissions.filter(codename="change_driverprofile").exists())
        self.assertFalse(role.permissions.filter(content_type__app_label="auth", codename="change_user").exists())
        change_url = reverse("admin:auth_group_change", args=[role.pk])
        self.assertEqual(self.client.get(change_url).status_code, 200)
        self.assertEqual(self.client.post(change_url, {"name": "Переименована", "permissions": [], "_save": "Сохранить"}).status_code, 302)
        role.refresh_from_db()
        self.assertEqual(role.name, "Переименована")
        self.assertEqual(role.permissions.count(), 0)
        self.assertEqual(self.client.post(reverse("admin:auth_group_delete", args=[role.pk]), {"post": "yes"}).status_code, 302)
        self.assertFalse(Group.objects.filter(pk=role.pk).exists())

    def test_command_does_not_overwrite_existing_roles(self):
        call_command("create_service_role", name="Новая роль из команды", verbosity=0)
        with self.assertRaises(CommandError):
            call_command("create_service_role", name=self.role.name, verbosity=0)

    def test_member_can_change_own_password(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse("admin:password_change"), {
            "old_password": "Test-only-8z!Long",
            "new_password1": "Another-test-only-2k!Long",
            "new_password2": "Another-test-only-2k!Long",
        })
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password("Another-test-only-2k!Long"))
