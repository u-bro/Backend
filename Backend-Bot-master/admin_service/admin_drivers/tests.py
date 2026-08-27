from unittest.mock import MagicMock, patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import connection
from django.test import RequestFactory, TransactionTestCase
from django.urls import reverse

from admin_car_photos.models import CarPhoto
from admin_cars.models import Car
from admin_ride_drivers_requests.models import RideDriversRequest
from admin_users.models import User

from .forms import DriverModerationForm
from .models import DriverProfile
from .views import moderation_detail


class DriverCarAdminLifecycleTests(TransactionTestCase):
    reset_sequences = True
    serialized_rollback = False
    models = (User, DriverProfile, Car, CarPhoto, RideDriversRequest)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        existing_tables = set(connection.introspection.table_names())
        cls.created_models = []
        with connection.schema_editor() as schema_editor:
            for model in cls.models:
                if model._meta.db_table not in existing_tables:
                    schema_editor.create_model(model)
                    cls.created_models.append(model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            for model in reversed(cls.created_models):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self):
        DriverProfile.objects.update(current_car_id=None)
        RideDriversRequest.objects.all().delete()
        CarPhoto.objects.all().delete()
        Car.objects.all().delete()
        DriverProfile.objects.all().delete()
        User.objects.all().delete()
        self.factory = RequestFactory()
        self.user = User.objects.create(
            first_name="Иван",
            last_name="Иванов",
            role_id=1,
            status="active",
        )
        self.profile = DriverProfile.objects.create(
            user_id=self.user.pk,
            first_name="Иван",
            last_name="Иванов",
            status="approved",
            classes_allowed=["light"],
        )

    def request(self, method="get", data=None):
        request = getattr(self.factory, method)(
            reverse("driver-moderation-detail", args=[self.profile.pk]),
            data=data or {},
        )
        request.user = MagicMock(
            is_authenticated=True,
            is_superuser=True,
            is_active=True,
            is_staff=True,
        )
        request.user.get_all_permissions.return_value = set()
        request.user.has_perm.return_value = True
        request.user.has_module_perms.return_value = True
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def call_view(self, request):
        empty_queryset = MagicMock()
        empty_queryset.order_by.return_value = empty_queryset
        empty_queryset.select_related.return_value = empty_queryset
        empty_queryset.values_list.return_value = []
        with (
            patch("admin_drivers.views._moderation_context", return_value={}),
            patch("admin_drivers.views.DriverDocument.objects.filter", return_value=empty_queryset),
            patch("admin_drivers.views.DriverProfileModeration.objects.filter", return_value=empty_queryset),
            patch("admin_drivers.views.DriverModerationInfo.objects.all", return_value=empty_queryset),
        ):
            return moderation_detail(request, self.profile.pk)

    @staticmethod
    def car_data(action, **overrides):
        data = {
            "action": action,
            "car_model": "Lada Vesta",
            "car_number": "А123АА77",
            "car_region": "77",
            "car_vin": "XTA12345678901234",
            "car_year": "2024",
        }
        data.update(overrides)
        return data

    def create_current_car(self):
        car = Car.objects.create(
            driver_profile_id=self.profile.pk,
            model="Lada Vesta",
            number="А123АА77",
            region="77",
            vin="XTA12345678901234",
            year="2024",
        )
        self.profile.current_car_id = car.pk
        self.profile.save(update_fields=["current_car_id"])
        return car

    def test_driver_without_car_only_shows_add_action(self):
        response = self.call_view(self.request())

        self.assertContains(response, "Добавить автомобиль")
        self.assertNotContains(response, "Текущий автомобиль")
        self.assertNotContains(response, "Автомобиль не выбран")
        self.assertNotContains(response, "Новая машина:")
        self.assertContains(response, 'id="car-editor" hidden')

    def test_create_car_persists_owner_current_car_and_reload_form(self):
        response = self.call_view(self.request("post", self.car_data("add_car")))

        self.assertEqual(response.status_code, 302)
        car = Car.objects.get()
        self.profile.refresh_from_db()
        self.assertEqual(car.driver_profile_id, self.profile.pk)
        self.assertEqual(self.profile.current_car_id, car.pk)

        reload_response = self.call_view(self.request())
        self.assertContains(reload_response, 'value="Lada Vesta"')
        self.assertContains(reload_response, 'value="А123АА77"')
        self.assertContains(reload_response, "Удалить автомобиль")
        self.assertNotContains(reload_response, "Добавить автомобиль")

    def test_existing_car_is_visible_on_first_open(self):
        self.create_current_car()

        response = self.call_view(self.request())

        self.assertContains(response, 'value="Lada Vesta"')
        self.assertContains(response, 'value="А123АА77"')
        self.assertContains(response, "Сохранить изменения")
        self.assertContains(response, "Удалить автомобиль")

    def test_update_car_does_not_create_second_car_and_reload_is_updated(self):
        car = self.create_current_car()
        response = self.call_view(self.request(
            "post",
            self.car_data(
                "update_car",
                car_model="Geely Monjaro",
                car_number="В456ВВ99",
                car_region="99",
                car_year="2025",
            ),
        ))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Car.objects.count(), 1)
        car.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(car.model, "Geely Monjaro")
        self.assertEqual(car.number, "В456ВВ99")
        self.assertEqual(self.profile.current_car_id, car.pk)

        reload_response = self.call_view(self.request())
        self.assertContains(reload_response, 'value="Geely Monjaro"')
        self.assertContains(reload_response, 'value="В456ВВ99"')

    def test_delete_car_clears_references_and_related_photos(self):
        car = self.create_current_car()
        photo = CarPhoto.objects.create(car_id=car.pk, type="FRONT")
        ride_request = RideDriversRequest.objects.create(
            driver_profile_id=self.profile.pk,
            car_id=car.pk,
            status="requested",
        )

        response = self.call_view(self.request("post", {"action": "delete_car"}))

        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        ride_request.refresh_from_db()
        self.assertIsNone(self.profile.current_car_id)
        self.assertIsNone(ride_request.car_id)
        self.assertFalse(Car.objects.filter(pk=car.pk).exists())
        self.assertFalse(CarPhoto.objects.filter(pk=photo.pk).exists())

        reload_response = self.call_view(self.request())
        self.assertContains(reload_response, "Добавить автомобиль")

    def test_moderation_form_requires_classes(self):
        form = DriverModerationForm(
            data={
                "first_name": "Иван",
                "last_name": "Иванов",
                "classes_allowed": [],
            },
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("classes_allowed", form.errors)

    def test_moderation_form_syncs_current_class(self):
        self.profile.approved = False
        self.profile.save(update_fields=["approved"])
        form = DriverModerationForm(
            data={
                "first_name": "Иван",
                "last_name": "Иванов",
                "classes_allowed": ["light", "vip"],
            },
            instance=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save_related_data()
        self.assertEqual(updated.classes_allowed, ["light", "vip"])
        self.assertEqual(updated.current_class, "vip")

    def test_approved_profile_fields_are_disabled_in_moderation_form(self):
        self.profile.approved = True
        self.profile.save(update_fields=["approved"])

        form = DriverModerationForm(instance=self.profile)

        self.assertTrue(all(field.disabled for field in form.fields.values()))
