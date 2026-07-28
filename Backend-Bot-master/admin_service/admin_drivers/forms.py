from datetime import datetime, time

from django import forms
from django.utils import timezone
from admin_cars.models import Car
from admin_users.models import User
from utils.schema_choices import RIDE_CLASS_CHOICES

from .models import DriverProfile


class DriverCarChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        details = " / ".join(value for value in (obj.model, obj.number, obj.region) if value)
        return f"#{obj.id} {details or 'Автомобиль без описания'}"


class DriverModerationForm(forms.ModelForm):
    phone = forms.CharField(label="Номер телефона", max_length=20, required=False)
    email = forms.EmailField(label="Email", max_length=255, required=False)
    city = forms.CharField(label="Город", max_length=100, required=False)
    birth_date = forms.DateField(
        label="Дата рождения",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    license_issued_at = forms.DateField(
        label="Дата выдачи прав",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    license_expires_at = forms.DateField(
        label="Дата окончания прав",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    classes_allowed = forms.MultipleChoiceField(
        label="Разрешённые классы",
        choices=RIDE_CLASS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    current_car_id = DriverCarChoiceField(
        label="Текущий автомобиль",
        queryset=Car.objects.none(),
        required=False,
        empty_label="Автомобиль не выбран",
        help_text="Выберите автомобиль этого водителя или заполните поля новой машины ниже.",
    )
    car_model = forms.CharField(label="Модель автомобиля", max_length=100, required=False)
    car_number = forms.CharField(label="Госномер", max_length=100, required=False)
    car_region = forms.CharField(label="Регион", max_length=20, required=False)
    car_vin = forms.CharField(label="VIN", max_length=100, required=False)
    car_year = forms.CharField(label="Год выпуска", max_length=10, required=False)
    new_car_model = forms.CharField(label="Новая машина: модель", max_length=100, required=False)
    new_car_number = forms.CharField(label="Новая машина: госномер", max_length=100, required=False)
    new_car_region = forms.CharField(label="Новая машина: регион", max_length=20, required=False)
    new_car_vin = forms.CharField(label="Новая машина: VIN", max_length=100, required=False)
    new_car_year = forms.CharField(label="Новая машина: год выпуска", max_length=10, required=False)

    class Meta:
        model = DriverProfile
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "photo_url",
            "phone",
            "email",
            "city",
            "license_number",
            "license_category",
            "license_issued_at",
            "license_expires_at",
            "experience_years",
            "classes_allowed",
            "current_class",
            "current_car_id",
            "car_model",
            "car_number",
            "car_region",
            "car_vin",
            "car_year",
            "new_car_model",
            "new_car_number",
            "new_car_region",
            "new_car_vin",
            "new_car_year",
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_cars = Car.objects.filter(driver_profile_id=self.instance.id).order_by("id")
        self.fields["current_car_id"].queryset = self.driver_cars
        user = User.objects.filter(id=self.instance.user_id).first() if self.instance.user_id else None
        if user:
            self.initial.update({
                "phone": user.phone,
                "email": user.email,
                "city": user.city,
            })

        classes_allowed = getattr(self.instance, "classes_allowed", None)
        if isinstance(classes_allowed, list):
            self.initial["classes_allowed"] = classes_allowed

        for field_name in ("birth_date", "license_issued_at", "license_expires_at"):
            value = getattr(self.instance, field_name, None)
            if value:
                if timezone.is_aware(value):
                    value = timezone.localtime(value)
                self.initial[field_name] = value.date()

        car = self._current_car()
        if car:
            self.initial.update({
                "current_car_id": car,
                "car_model": car.model,
                "car_number": car.number,
                "car_region": car.region,
                "car_vin": car.vin,
                "car_year": car.year,
            })

    def _current_car(self):
        if self.instance.current_car_id:
            return Car.objects.filter(id=self.instance.current_car_id, driver_profile_id=self.instance.id).first()
        return Car.objects.filter(driver_profile_id=self.instance.id).order_by("id").first()

    def clean(self):
        cleaned = super().clean()
        user_id = self.instance.user_id
        phone = cleaned.get("phone")
        email = cleaned.get("email")
        if phone and User.objects.filter(phone=phone).exclude(id=user_id).exists():
            self.add_error("phone", "Этот номер уже используется другим пользователем.")
        if email and User.objects.filter(email=email).exclude(id=user_id).exists():
            self.add_error("email", "Этот email уже используется другим пользователем.")

        selected_car = cleaned.get("current_car_id")
        if selected_car and selected_car.driver_profile_id != self.instance.id:
            self.add_error("current_car_id", "Автомобиль не принадлежит этому водителю.")

        new_car_model = (cleaned.get("new_car_model") or "").strip()
        new_car_number = (cleaned.get("new_car_number") or "").strip()
        if bool(new_car_model) != bool(new_car_number):
            self.add_error("new_car_model", "Для добавления машины укажите модель и госномер.")
            self.add_error("new_car_number", "Для добавления машины укажите модель и госномер.")
        return cleaned

    def save_related_data(self, commit=True):
        profile = super().save(commit=False)
        user = User.objects.get(id=profile.user_id)

        for field in ("first_name", "last_name", "middle_name", "photo_url"):
            value = self.cleaned_data.get(field)
            setattr(profile, field, value)
            setattr(user, field, value)

        for field in ("phone", "email", "city"):
            setattr(user, field, self.cleaned_data.get(field) or None)

        for field_name in ("birth_date", "license_issued_at", "license_expires_at"):
            value = self.cleaned_data.get(field_name)
            value = datetime.combine(value, time.min) if value else None
            setattr(profile, field_name, timezone.make_aware(value) if value else None)

        if commit:
            user.save(update_fields=["first_name", "last_name", "middle_name", "photo_url", "phone", "email", "city"])

        selected_car = self.cleaned_data.get("current_car_id")
        new_car_values = {
            "model": (self.cleaned_data.get("new_car_model") or "").strip(),
            "number": (self.cleaned_data.get("new_car_number") or "").strip(),
            "region": (self.cleaned_data.get("new_car_region") or "").strip() or None,
            "vin": (self.cleaned_data.get("new_car_vin") or "").strip() or None,
            "year": (self.cleaned_data.get("new_car_year") or "").strip() or None,
        }
        if new_car_values["model"] and new_car_values["number"]:
            selected_car = Car.objects.create(driver_profile_id=profile.id, **new_car_values)

        car_values = {
            "model": self.cleaned_data.get("car_model"),
            "number": self.cleaned_data.get("car_number"),
            "region": self.cleaned_data.get("car_region"),
            "vin": self.cleaned_data.get("car_vin"),
            "year": self.cleaned_data.get("car_year"),
        }
        if selected_car:
            if not new_car_values["model"]:
                Car.objects.filter(id=selected_car.id, driver_profile_id=profile.id).update(**car_values)
            profile.current_car_id = selected_car.id
        else:
            profile.current_car_id = None

        if commit:
            profile.save()

        return profile
