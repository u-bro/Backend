import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings

from .admin import AdminPushNotificationAdmin
from .client import PushAPIError, PushAPITimeout, send_push
from .forms import PushNotificationForm
from .models import AdminPushNotification
from .views import can_send_push, send_push_view


def make_user(*, superuser=False, groups=()):
    group_manager = MagicMock()
    group_manager.filter.return_value.exists.return_value = "Admin" in groups
    return SimpleNamespace(
        id=7,
        is_active=True,
        is_staff=True,
        is_superuser=superuser,
        groups=group_manager,
        get_full_name=lambda: "Admin User",
        get_username=lambda: "admin",
    )


class PushAccessTests(SimpleTestCase):
    def test_only_admin_group_or_superuser_can_send(self):
        self.assertTrue(can_send_push(make_user(groups=("Admin",))))
        self.assertTrue(can_send_push(make_user(superuser=True)))
        self.assertFalse(can_send_push(make_user(groups=("Operator",))))
        self.assertFalse(can_send_push(AnonymousUser()))

    def test_operator_gets_not_found(self):
        request = RequestFactory().get("/admin/push-notifications/send/")
        request.user = make_user(groups=("Operator",))
        with self.assertRaises(Http404):
            send_push_view(request)

    def test_history_admin_is_read_only_and_admin_only(self):
        model_admin = AdminPushNotificationAdmin(AdminPushNotification, admin.site)
        request = SimpleNamespace(user=make_user(groups=("Admin",)))
        self.assertTrue(model_admin.has_view_permission(request))
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))


class PushFormTests(SimpleTestCase):
    @patch("admin_push_notifications.forms.User.objects.order_by")
    def test_mass_send_requires_confirmation(self, order_by):
        order_by.return_value = MagicMock()
        form = PushNotificationForm(data={"audience": "all", "title": "Title", "body": "Body"})
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_all", form.errors)

    @patch("admin_push_notifications.forms.User.objects.order_by")
    def test_single_send_requires_user(self, order_by):
        order_by.return_value = MagicMock()
        form = PushNotificationForm(data={"audience": "user", "title": "Title", "body": "Body"})
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)


class PushClientTests(SimpleTestCase):
    @override_settings(PUSH_API_BASE_URL="http://backend:5000", PUSH_API_TIMEOUT=12)
    @patch("admin_push_notifications.client.requests.post")
    def test_client_uses_internal_token(self, post):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"history_id": 1}
        payload = {"audience": "all", "title": "Title", "body": "Body"}

        with patch.dict(os.environ, {"PUSH_INTERNAL_TOKEN": "secret"}):
            self.assertEqual(send_push(payload), {"history_id": 1})

        post.assert_called_once_with(
            "http://backend:5000/api/v1/internal/push/send",
            json=payload,
            headers={"X-Push-Internal-Token": "secret"},
            timeout=12,
        )

    def test_missing_token_fails_without_request(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PushAPIError):
                send_push({})

    @override_settings(PUSH_API_BASE_URL="http://backend:5000", PUSH_API_TIMEOUT=12)
    @patch("admin_push_notifications.client.requests.post", side_effect=requests.Timeout)
    def test_timeout_has_unknown_result_message(self, post):
        with patch.dict(os.environ, {"PUSH_INTERNAL_TOKEN": "secret"}):
            with self.assertRaisesRegex(PushAPITimeout, "Не повторяйте"):
                send_push({})
