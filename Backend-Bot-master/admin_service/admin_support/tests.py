import os
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings

from .client import SupportAPIError, support_action
from .models import SupportConversation
from .views import can_access_support, can_change_support, operator_name, with_unread


class SupportAccessTests(SimpleTestCase):
    def test_superuser_and_named_groups_have_access(self):
        group_filter = SimpleNamespace(exists=lambda: True)
        operator = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_superuser=False,
            groups=SimpleNamespace(filter=lambda **kwargs: group_filter),
        )
        superuser = SimpleNamespace(is_active=True, is_staff=True, is_superuser=True)

        self.assertTrue(can_access_support(operator))
        self.assertTrue(can_access_support(superuser))
        self.assertFalse(can_access_support(AnonymousUser()))

    def test_operator_display_name_falls_back_to_username(self):
        user = SimpleNamespace(get_full_name=lambda: "", get_username=lambda: "operator")
        self.assertEqual(operator_name(user), "operator")

    def test_change_access_requires_permission(self):
        group_filter = SimpleNamespace(exists=lambda: True)
        operator = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_superuser=False,
            groups=SimpleNamespace(filter=lambda **kwargs: group_filter),
            has_perm=lambda permission: permission == "admin_support.change_supportconversation",
        )

        self.assertTrue(can_change_support(operator))

    def test_unread_semantics_match_backend(self):
        sql = str(with_unread(SupportConversation.objects.all()).query)
        self.assertIn("sender_type", sql)
        self.assertIn("USER", sql)
        self.assertIn("last_read_message_id", sql)


class SupportClientTests(SimpleTestCase):
    @override_settings(SUPPORT_API_BASE_URL="http://backend:5000", SUPPORT_API_TIMEOUT=4)
    @patch("admin_support.client.requests.post")
    def test_reply_uses_internal_token_and_operator_header(self, post):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"id": 5}
        payload = {"text": "Ответ", "idempotency_key": "django-12345678"}

        with patch.dict(os.environ, {"SUPPORT_INTERNAL_TOKEN": "secret"}):
            support_action(7, "messages", "Operator Name", payload)

        post.assert_called_once_with(
            "http://backend:5000/api/v1/internal/support/conversations/7/messages",
            json=payload,
            headers={
                "X-Support-Internal-Token": "secret",
                "X-Support-Operator": "Operator Name",
                "X-Support-Operator-Utf8": "Operator%20Name",
            },
            timeout=4,
        )

    @override_settings(SUPPORT_API_BASE_URL="http://backend:5000", SUPPORT_API_TIMEOUT=4)
    @patch("admin_support.client.requests.post")
    def test_unicode_operator_is_safe_for_http_transport(self, post):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"id": 9}
        for name in ("Иван Петров", "Оператор 👋", "100% Support", "И" * 160):
            with self.subTest(name=name), patch.dict(os.environ, {"SUPPORT_INTERNAL_TOKEN": "secret"}):
                support_action(9, "read", name, {"up_to_message_id": 1})
                headers = post.call_args.kwargs["headers"]
                for value in headers.values():
                    value.encode("ascii")
                self.assertEqual(unquote(headers["X-Support-Operator-Utf8"]), name[:150])

    def test_missing_internal_token_fails_without_request(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SupportAPIError):
                support_action(1, "close", "operator")


class SupportRouteTests(SimpleTestCase):
    def test_mutating_route_is_post_only_and_csrf_middleware_is_enabled(self):
        from admin_project.settings import MIDDLEWARE
        from .views import conversation_action

        request = RequestFactory().get("/admin/support/1/close/")
        response = conversation_action(request, 1, "close")
        self.assertEqual(response.status_code, 405)
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", MIDDLEWARE)
