from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib import admin
from django.test import SimpleTestCase
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

from .settings import JAZZMIN_SETTINGS


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

    @patch("admin_cars.admin.CarPhoto.objects.filter")
    def test_car_gallery_and_empty_state(self, filter_mock):
        queryset = MagicMock()
        filter_mock.return_value = queryset
        model_admin = CarAdmin(Car, admin.site)
        car = SimpleNamespace(pk=42)

        queryset.order_by.return_value = []
        self.assertEqual(model_admin.photo_gallery(car), "Фотографии не загружены.")

        queryset.order_by.return_value = [
            SimpleNamespace(
                photo_url="https://cdn.example/car.jpg",
                type="CAR_FRONT",
                description="Спереди",
                status="approved",
            )
        ]
        gallery = str(model_admin.photo_gallery(car))
        self.assertIn("https://cdn.example/car.jpg", gallery)
        self.assertIn("CAR_FRONT", gallery)

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

    def test_custom_templates_load(self):
        for template_name in (
            "admin_drivers/moderation_detail.html",
            "admin/admin_cars/car/change_form.html",
            "admin/admin_users/user/change_form.html",
        ):
            with self.subTest(template=template_name):
                self.assertIsNotNone(get_template(template_name))
