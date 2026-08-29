import json
import os
import subprocess
import sys
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
from .views import can_send_push, send_push_view, user_search


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
    def test_mass_send_requires_confirmation(self):
        form = PushNotificationForm(data={"audience": "all", "title": "Title", "body": "Body"})
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_all", form.errors)

    def test_single_send_requires_user(self):
        form = PushNotificationForm(data={"audience": "user", "title": "Title", "body": "Body"})
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)


class PushUserSearchTests(SimpleTestCase):
    def test_operator_cannot_search_users(self):
        request = RequestFactory().get("/admin/push-notifications/users/search/", {"q": "Иван"})
        request.user = make_user(groups=("Operator",))
        with self.assertRaises(Http404):
            user_search(request)

    @patch("admin_push_notifications.views.User.objects.filter")
    def test_short_query_returns_empty_without_database_search(self, user_filter):
        request = RequestFactory().get("/admin/push-notifications/users/search/", {"q": "И"})
        request.user = make_user(groups=("Admin",))

        response = user_search(request)

        self.assertEqual(json.loads(response.content), {"results": []})
        user_filter.assert_not_called()

    @patch("admin_push_notifications.views.User.objects.filter")
    def test_search_returns_compact_user_labels_and_limits_results(self, user_filter):
        ordered = MagicMock()
        ordered.__getitem__.return_value = [
            SimpleNamespace(
                id=42,
                first_name="Иван",
                last_name="Петров",
                middle_name=None,
                phone="+7 (999) 123-45-67",
                email="ivan@example.com",
                is_active=False,
            )
        ]
        user_filter.return_value.order_by.return_value = ordered
        request = RequestFactory().get("/admin/push-notifications/users/search/", {"q": "999123"})
        request.user = make_user(groups=("Admin",))

        response = user_search(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["results"][0]["id"], 42)
        self.assertIn("Петров Иван", payload["results"][0]["label"])
        self.assertIn("+7 (999) 123-45-67", payload["results"][0]["label"])
        self.assertFalse(payload["results"][0]["is_active"])
        ordered.__getitem__.assert_called_once_with(slice(None, 20, None))


class PushClientTests(SimpleTestCase):
    def test_settings_loads_internal_token_from_environment(self):
        token = "regression-token-from-environment"
        environment = os.environ.copy()
        environment["PUSH_INTERNAL_TOKEN"] = token

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os, sys; from admin_project import settings; "
                "sys.exit(0 if settings.PUSH_INTERNAL_TOKEN == os.environ['PUSH_INTERNAL_TOKEN'] else 1)",
            ],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    @override_settings(
        PUSH_API_BASE_URL="http://backend:5000",
        PUSH_API_TIMEOUT=12,
        PUSH_INTERNAL_TOKEN="secret-from-settings",
    )
    @patch("admin_push_notifications.client.requests.post")
    def test_client_uses_internal_token(self, post):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"history_id": 1}
        payload = {"audience": "all", "title": "Title", "body": "Body"}

        self.assertEqual(send_push(payload), {"history_id": 1})

        post.assert_called_once_with(
            "http://backend:5000/api/v1/internal/push/send",
            json=payload,
            headers={"X-Push-Internal-Token": "secret-from-settings"},
            timeout=12,
        )

    @override_settings(PUSH_INTERNAL_TOKEN=None)
    @patch("admin_push_notifications.client.requests.post")
    def test_missing_token_fails_without_request(self, post):
        with self.assertRaisesRegex(PushAPIError, "PUSH_INTERNAL_TOKEN не настроен"):
            send_push({})
        post.assert_not_called()

    @override_settings(
        PUSH_API_BASE_URL="http://backend:5000",
        PUSH_API_TIMEOUT=12,
        PUSH_INTERNAL_TOKEN="secret-from-settings",
    )
    @patch("admin_push_notifications.client.requests.post", side_effect=requests.Timeout)
    def test_timeout_has_unknown_result_message(self, post):
        with self.assertRaisesRegex(PushAPITimeout, "Не повторяйте"):
            send_push({})

    @override_settings(
        PUSH_API_BASE_URL="http://backend:5000",
        PUSH_API_TIMEOUT=12,
        PUSH_INTERNAL_TOKEN="secret-from-settings",
    )
    @patch("admin_push_notifications.client.requests.post")
    def test_duplicate_error_exposes_history(self, post):
        post.return_value.status_code = 409
        post.return_value.json.return_value = {
            "detail": {
                "code": "ADMIN_PUSH_DUPLICATE_RECENT",
                "history_id": 42,
            }
        }

        with self.assertRaises(PushAPIError) as exc_info:
            send_push({})

        self.assertEqual(exc_info.exception.code, "ADMIN_PUSH_DUPLICATE_RECENT")
        self.assertEqual(exc_info.exception.history_id, 42)
