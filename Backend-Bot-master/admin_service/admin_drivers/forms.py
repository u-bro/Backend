from django import forms
from admin_cars.models import Car
from admin_users.models import User
from utils.schema_choices import RIDE_CLASS_CHOICES

from .models import DriverProfile


class DriverModerationForm(forms.ModelForm):
    phone = forms.CharField(label="Номер телефона", max_length=20, required=False)
    email = forms.EmailField(label="Email", max_length=255, required=False)
    city = forms.CharField(label="Город", max_length=100, required=False)
    classes_allowed = forms.MultipleChoiceField(
        label="Разрешённые классы",
        choices=RIDE_CLASS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    current_car_id = forms.IntegerField(label="ID текущего автомобиля", required=False, min_value=1)
    car_model = forms.CharField(label="Модель автомобиля", max_length=100, required=False)
    car_number = forms.CharField(label="Госномер", max_length=100, required=False)
    car_region = forms.CharField(label="Регион", max_length=20, required=False)
    car_vin = forms.CharField(label="VIN", max_length=100, required=False)
    car_year = forms.CharField(label="Год выпуска", max_length=10, required=False)

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
        )
        widgets = {
            "birth_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "license_issued_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "license_expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        car = self._current_car()
        if car:
            self.initial.update({
                "current_car_id": car.id,
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

        car_id = cleaned.get("current_car_id")
        if car_id and not Car.objects.filter(id=car_id, driver_profile_id=self.instance.id).exists():
            self.add_error("current_car_id", "Автомобиль не принадлежит этому водителю.")
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

        if commit:
            profile.save()
            user.save(update_fields=["first_name", "last_name", "middle_name", "photo_url", "phone", "email", "city"])

        car_id = self.cleaned_data.get("current_car_id")
        car_values = {
            "model": self.cleaned_data.get("car_model"),
            "number": self.cleaned_data.get("car_number"),
            "region": self.cleaned_data.get("car_region"),
            "vin": self.cleaned_data.get("car_vin"),
            "year": self.cleaned_data.get("car_year"),
        }
        if car_id:
            Car.objects.filter(id=car_id, driver_profile_id=profile.id).update(**car_values)
        elif any(car_values.values()):
            car = Car.objects.filter(driver_profile_id=profile.id).order_by("id").first()
            if car:
                Car.objects.filter(id=car.id).update(**car_values)
            else:
                car = Car.objects.create(driver_profile_id=profile.id, **car_values)
            profile.current_car_id = car.id
            profile.save(update_fields=["current_car_id"])

        return profile
