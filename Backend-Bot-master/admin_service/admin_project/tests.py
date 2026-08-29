from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django.template.loader import get_template
from django.urls import reverse

from admin_cars.admin import CarAdmin
from admin_cars.models import Car
from admin_car_photos.admin import CarPhotoAdmin
from admin_car_photos.models import CarPhoto
from admin_chat_messages.admin import ChatMessageAdmin
from admin_chat_messages.models import ChatMessage
from admin_commission_payments.admin import CommissionPaymentAdmin
from admin_commission_payments.models import CommissionPayment
from admin_driver_locations.admin import DriverLocationAdmin
from admin_driver_locations.models import DriverLocation
from admin_drivers.admin import DriverProfileAdmin
from admin_drivers.models import DriverProfile
from admin_drivers.views import _build_car_cards
from admin_ride_drivers_requests.admin import RideDriversRequestAdmin
from admin_ride_drivers_requests.models import RideDriversRequest
from admin_ride_status_history.admin import RideStatusHistoryAdmin
from admin_ride_status_history.models import RideStatusHistory
from admin_rides.admin import RideAdmin
from admin_rides.models import Ride
from admin_users.admin import UserAdmin
from admin_users.models import User
from utils.admin_links import admin_change_link, driver_profile_link, safe_external_url

from .settings import (
    DRIVER_PROFILE_INITIAL_RATING_AVG,
    DRIVER_PROFILE_INITIAL_RATING_COUNT,
    JAZZMIN_SETTINGS,
)


class AdminLinkTests(SimpleTestCase):
    def test_standard_and_empty_links(self):
        self.assertEqual(admin_change_link(None, "admin_users", "user"), "—")
        link = str(admin_change_link(7, "admin_users", "user"))
        self.assertIn(reverse("admin:admin_users_user_change", args=[7]), link)
        self.assertIn(">7</a>", link)

    def test_driver_link_uses_extended_detail(self):
        link = str(driver_profile_link(15))
        self.assertIn(reverse("driver-moderation-detail", args=[15]), link)
        self.assertIn("from=profiles", link)

    def test_external_urls_allow_only_http(self):
        self.assertEqual(safe_external_url("https://cdn.example/photo.jpg"), "https://cdn.example/photo.jpg")
        self.assertEqual(safe_external_url("http://cdn.example/photo.jpg"), "http://cdn.example/photo.jpg")
        self.assertIsNone(safe_external_url("javascript:alert(1)"))
        self.assertIsNone(safe_external_url("/relative/photo.jpg"))

    def test_all_requested_admin_columns_are_links(self):
        cases = (
            (CarAdmin(Car, admin.site), "driver_profile_id_link", SimpleNamespace(driver_profile_id=1), "/admin/driver-moderation/1/"),
            (RideDriversRequestAdmin(RideDriversRequest, admin.site), "ride_id_link", SimpleNamespace(ride_id=1), "/admin/admin_rides/ride/1/change/"),
            (RideDriversRequestAdmin(RideDriversRequest, admin.site), "driver_profile_id_link", SimpleNamespace(driver_profile_id=2), "/admin/driver-moderation/2/"),
            (CommissionPaymentAdmin(CommissionPayment, admin.site), "ride_id_link", SimpleNamespace(ride_id=3), "/admin/admin_rides/ride/3/change/"),
            (CommissionPaymentAdmin(CommissionPayment, admin.site), "user_id_link", SimpleNamespace(user_id=3), "/admin/admin_users/user/3/change/"),
            (DriverProfileAdmin(DriverProfile, admin.site), "user_id_link", SimpleNamespace(user_id=4), "/admin/admin_users/user/4/change/"),
            (RideStatusHistoryAdmin(RideStatusHistory, admin.site), "ride_id_link", SimpleNamespace(ride_id=4), "/admin/admin_rides/ride/4/change/"),
            (DriverLocationAdmin(DriverLocation, admin.site), "driver_profile_id_link", SimpleNamespace(driver_profile_id=5), "/admin/driver-moderation/5/"),
            (RideAdmin(Ride, admin.site), "client_id_link", SimpleNamespace(client_id=6), "/admin/admin_users/user/6/change/"),
            (RideAdmin(Ride, admin.site), "driver_profile_id_link", SimpleNamespace(driver_profile_id=6), "/admin/driver-moderation/6/"),
            (ChatMessageAdmin(ChatMessage, admin.site), "ride_id_link", SimpleNamespace(ride_id=7), "/admin/admin_rides/ride/7/change/"),
            (ChatMessageAdmin(ChatMessage, admin.site), "sender_id_link", SimpleNamespace(sender_id=7), "/admin/admin_users/user/7/change/"),
            (ChatMessageAdmin(ChatMessage, admin.site), "receiver_id_link", SimpleNamespace(receiver_id=8), "/admin/admin_users/user/8/change/"),
        )
        for model_admin, method_name, obj, expected_url in cases:
            with self.subTest(method=method_name):
                self.assertIn(expected_url, str(getattr(model_admin, method_name)(obj)))


class DriverDetailTests(SimpleTestCase):
    def test_new_driver_profile_rating_defaults(self):
        self.assertEqual(
            DriverProfile._meta.get_field("rating_avg").default,
            DRIVER_PROFILE_INITIAL_RATING_AVG,
        )
        self.assertEqual(
            DriverProfile._meta.get_field("rating_count").default,
            DRIVER_PROFILE_INITIAL_RATING_COUNT,
        )

    def test_standard_change_view_redirects_to_extended_detail(self):
        model_admin = DriverProfileAdmin(DriverProfile, admin.site)
        response = model_admin.change_view(SimpleNamespace(), "23")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'{reverse("driver-moderation-detail", args=[23])}?from=profiles')

    def test_car_cards_keep_photos_separated_and_mark_current(self):
        cars = [SimpleNamespace(id=10), SimpleNamespace(id=20)]
        photo_a = SimpleNamespace(id=1, car_id=10, photo_url="https://cdn.example/1.jpg")
        photo_b = SimpleNamespace(id=2, car_id=20, photo_url="https://cdn.example/2.jpg")
        photo_c = SimpleNamespace(id=3, car_id=10, photo_url="https://cdn.example/3.jpg")

        cards = _build_car_cards(cars, [photo_a, photo_b, photo_c], current_car_id=20)

        self.assertEqual([item["photo"].id for item in cards[0]["photos"]], [1, 3])
        self.assertEqual([item["photo"].id for item in cards[1]["photos"]], [2])
        self.assertFalse(cards[0]["is_current"])
        self.assertTrue(cards[1]["is_current"])


class ImagePreviewTests(SimpleTestCase):
    def test_user_preview_and_empty_state(self):
        model_admin = UserAdmin(User, admin.site)
        self.assertEqual(model_admin.photo_preview(SimpleNamespace(photo_url=None)), "Изображение не загружено.")
        preview = str(model_admin.photo_preview(SimpleNamespace(photo_url="https://cdn.example/avatar.jpg")))
        self.assertIn("https://cdn.example/avatar.jpg", preview)
        self.assertIn("user-avatar", preview)

    @patch("admin_cars.admin.DriverDocument.objects.filter")
    @patch("admin_cars.admin.DriverProfile.objects.filter")
    @patch("admin_cars.admin.CarPhoto.objects.filter")
    def test_current_car_gallery_combines_photos_and_driver_documents(
        self,
        photo_filter_mock,
        profile_filter_mock,
        document_filter_mock,
    ):
        photo_queryset = MagicMock()
        photo_filter_mock.return_value = photo_queryset
        profile_filter_mock.return_value.exists.return_value = True
        document_queryset = MagicMock()
        document_filter_mock.return_value = document_queryset
        model_admin = CarAdmin(Car, admin.site)
        car = SimpleNamespace(pk=42, driver_profile_id=15)

        photo_queryset.order_by.return_value = []
        document_queryset.order_by.return_value = []
        self.assertEqual(model_admin.photo_gallery(car), "Фотографии не загружены.")

        photo_queryset.order_by.return_value = [
            SimpleNamespace(
                photo_url="https://cdn.example/car.jpg",
                type="CAR_FRONT",
                description="Спереди",
                status="approved",
            )
        ]
        document_queryset.order_by.return_value = [
            SimpleNamespace(
                id=99,
                doc_type="CAR_PHOTO_FRONT",
                file_bucket_key="drivers/15/car-front.jpg",
                status="approved",
                created_at=None,
            )
        ]
        gallery = str(model_admin.photo_gallery(car))
        self.assertIn("https://cdn.example/car.jpg", gallery)
        self.assertIn("CAR_FRONT", gallery)
        self.assertIn("CAR_PHOTO_FRONT", gallery)
        self.assertIn(reverse("admin:admin_driver_document_preview", args=[99]), gallery)
        document_filter_mock.assert_called_with(
            driver_profile_id=15,
            doc_type__startswith="CAR_PHOTO_",
        )

    @patch("admin_cars.admin.DriverDocument.objects.filter")
    @patch("admin_cars.admin.DriverProfile.objects.filter")
    @patch("admin_cars.admin.CarPhoto.objects.filter")
    def test_non_current_car_does_not_show_profile_documents(
        self,
        photo_filter_mock,
        profile_filter_mock,
        document_filter_mock,
    ):
        photo_queryset = MagicMock()
        photo_queryset.order_by.return_value = []
        photo_filter_mock.return_value = photo_queryset
        profile_filter_mock.return_value.exists.return_value = False

        gallery = str(CarAdmin(Car, admin.site).photo_gallery(
            SimpleNamespace(pk=42, driver_profile_id=15)
        ))

        self.assertIn("только у текущего автомобиля", gallery)
        document_filter_mock.assert_not_called()

    def test_direct_car_photo_admin_rejects_unsafe_url(self):
        model_admin = CarPhotoAdmin(CarPhoto, admin.site)
        photo = SimpleNamespace(photo_url="javascript:alert(1)")
        self.assertEqual(model_admin.photo_preview(photo), "Нет фото")
        self.assertEqual(model_admin.photo_link(photo), "Нет фото")


class SidebarSettingsTests(SimpleTestCase):
    def test_sidebar_groups_and_hidden_apps(self):
        hidden = set(JAZZMIN_SETTINGS["hide_apps"])
        self.assertTrue({"admin_car_photos", "admin_driver_documents", "admin_users"}.issubset(hidden))

        driver_links = [item["name"] for item in JAZZMIN_SETTINGS["custom_links"]["admin_drivers"]]
        self.assertEqual(driver_links[-1], "Причины модераций")
        self.assertIn("Автомобили", driver_links)
        self.assertIn("Локации водителей", driver_links)

        auth_links = [item["name"] for item in JAZZMIN_SETTINGS["custom_links"]["auth"]]
        self.assertEqual(auth_links, ["Администраторы", "Пользователи"])
        self.assertEqual(JAZZMIN_SETTINGS["order_with_respect_to"][-1], "axes")
        top_links = [item["name"] for item in JAZZMIN_SETTINGS["topmenu_links"]]
        self.assertEqual(top_links.index("Поддержка"), top_links.index("Модерация водителей") + 1)
        self.assertEqual(JAZZMIN_SETTINGS["custom_css"], "admin_support/support.css")
        self.assertEqual(JAZZMIN_SETTINGS["custom_js"], "admin_support/support.js")


class ModelAdminCheckTests(SimpleTestCase):
    def test_changed_admin_classes_pass_system_checks(self):
        model_admins = (
            CarAdmin(Car, admin.site),
            CarPhotoAdmin(CarPhoto, admin.site),
            UserAdmin(User, admin.site),
            DriverProfileAdmin(DriverProfile, admin.site),
            RideDriversRequestAdmin(RideDriversRequest, admin.site),
            CommissionPaymentAdmin(CommissionPayment, admin.site),
            RideStatusHistoryAdmin(RideStatusHistory, admin.site),
            DriverLocationAdmin(DriverLocation, admin.site),
            RideAdmin(Ride, admin.site),
            ChatMessageAdmin(ChatMessage, admin.site),
        )
        errors = [error for model_admin in model_admins for error in model_admin.check()]
        self.assertEqual(errors, [])

    @patch("admin_cars.admin.DriverProfile.objects.filter")
    def test_car_admin_denies_changes_for_approved_driver(self, profile_filter):
        profile_filter.return_value.exists.return_value = True
        request = SimpleNamespace(user=MagicMock())
        request.user.groups.filter.return_value.exists.return_value = True
        model_admin = CarAdmin(Car, admin.site)
        car = SimpleNamespace(driver_profile_id=7)

        self.assertFalse(model_admin.has_change_permission(request, car))
        self.assertFalse(model_admin.has_delete_permission(request, car))

    @patch("admin_car_photos.admin.DriverProfile.objects.filter")
    @patch("admin_car_photos.admin.Car.objects.filter")
    def test_car_photo_admin_denies_changes_for_approved_driver(self, car_filter, profile_filter):
        car_filter.return_value.values_list.return_value.first.return_value = 7
        profile_filter.return_value.exists.return_value = True
        request = SimpleNamespace(user=MagicMock())
        request.user.groups.filter.return_value.exists.return_value = True
        model_admin = CarPhotoAdmin(CarPhoto, admin.site)
        photo = SimpleNamespace(car_id=9)

        self.assertFalse(model_admin.has_change_permission(request, photo))
        self.assertFalse(model_admin.has_delete_permission(request, photo))

    def test_custom_templates_load(self):
        for template_name in (
            "admin_drivers/moderation_detail.html",
            "admin/admin_cars/car/change_form.html",
            "admin/admin_users/user/change_form.html",
            "admin_support/workspace.html",
        ):
            with self.subTest(template=template_name):
                self.assertIsNotNone(get_template(template_name))


class SupportWorkspaceTemplateTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/support/")
        self.request.user = AnonymousUser()
        self.template = get_template("admin_support/workspace.html")

    def context(self, **overrides):
        context = {
            **admin.site.each_context(self.request),
            "title": "Поддержка",
            "conversations": [],
            "selected": None,
            "selected_messages": [],
            "selected_status": "OPEN",
            "search_query": "",
            "unread_only": False,
            "open_count": 0,
            "new_count": 0,
            "closed_count": 0,
        }
        context.update(overrides)
        return context

    def test_empty_workspace_renders_filters_search_and_selection_prompt(self):
        rendered = self.template.render(self.context(open_count=4, new_count=2, closed_count=7), self.request)

        self.assertIn("Центр обращений", rendered)
        self.assertIn("Имя, телефон или #ID", rendered)
        self.assertIn("Выберите обращение", rendered)
        self.assertIn("Открытые", rendered)
        self.assertIn("Новые", rendered)
        self.assertIn("Закрытые", rendered)

    def test_selected_dialog_renders_message_states_and_preserves_filters(self):
        created_at = datetime(2026, 8, 24, 12, 30, tzinfo=timezone.utc)
        attachment = SimpleNamespace(
            attachment_type="image",
            file_name="photo.jpg",
            mime_type="image/jpeg",
            file_size=2048,
            safe_url="https://files.example/photo.jpg",
        )
        empty_attachments = SimpleNamespace(all=lambda: [])
        image_attachments = SimpleNamespace(all=lambda: [attachment])
        selected_messages = [
            SimpleNamespace(id=1, sender_type="USER", text="Нужна помощь", created_at=created_at, delivery_status="SENT", operator_name=None, attachments=image_attachments),
            SimpleNamespace(id=2, sender_type="OPERATOR", text="Уточняем информацию", created_at=created_at, delivery_status="FAILED", operator_name="Анна", attachments=empty_attachments),
            SimpleNamespace(id=3, sender_type="BOT", text="Автоматический ответ", created_at=created_at, delivery_status="SENT", operator_name=None, attachments=empty_attachments),
            SimpleNamespace(id=4, sender_type="SYSTEM", text="Диалог создан", created_at=created_at, delivery_status="SENT", operator_name=None, attachments=empty_attachments),
        ]
        conversation = SimpleNamespace(
            id=42,
            contact_label="Иван Петров",
            contact_phone="+79990000000",
            max_user_id=101,
            source="APP",
            get_source_display=lambda: "Приложение",
            status="OPEN",
            unread_count=3,
            visible_last_inbound_id=1,
            latest_sender="USER",
            latest_text="Нужна помощь",
            latest_created_at=created_at,
            updated_at=created_at,
        )
        rendered = self.template.render(
            self.context(
                conversations=[conversation],
                selected=conversation,
                selected_messages=selected_messages,
                selected_status="OPEN",
                search_query="Иван Петров",
                unread_only=True,
                open_count=1,
                new_count=1,
            ),
            self.request,
        )

        self.assertIn("support-conversation-item active unread", rendered)
        self.assertIn("Непрочитанных сообщений: 3", rendered)
        for sender_type in ("user", "operator", "bot", "system"):
            self.assertIn(f"support-message {sender_type}", rendered)
        self.assertIn("Не доставлено", rendered)
        self.assertIn("Повторить отправку", rendered)
        self.assertIn("photo.jpg", rendered)
        self.assertIn('class="support-image-attachment"', rendered)
        self.assertIn('src="https://files.example/photo.jpg"', rendered)
        self.assertIn('loading="lazy"', rendered)
        self.assertIn("status=OPEN&amp;unread=1&amp;q=%D0%98%D0%B2%D0%B0%D0%BD%20%D0%9F%D0%B5%D1%82%D1%80%D0%BE%D0%B2", rendered)
