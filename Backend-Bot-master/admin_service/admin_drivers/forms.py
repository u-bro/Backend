from datetime import datetime, time

from django import forms
from django.utils import timezone
from admin_users.models import User
from utils.schema_choices import RIDE_CLASS_CHOICES

from .models import DriverProfile


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
        )

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

        for field_name in ("birth_date", "license_issued_at", "license_expires_at"):
            value = getattr(self.instance, field_name, None)
            if value:
                if timezone.is_aware(value):
                    value = timezone.localtime(value)
                self.initial[field_name] = value.date()

    def clean(self):
        cleaned = super().clean()
        user_id = self.instance.user_id
        phone = cleaned.get("phone")
        email = cleaned.get("email")
        if phone and User.objects.filter(phone=phone).exclude(id=user_id).exists():
            self.add_error("phone", "Этот номер уже используется другим пользователем.")
        if email and User.objects.filter(email=email).exclude(id=user_id).exists():
            self.add_error("email", "Этот email уже используется другим пользователем.")

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

        if commit:
            profile.save()

        return profile


class DriverCarForm(forms.Form):
    car_model = forms.CharField(label="Модель", max_length=100)
    car_number = forms.CharField(label="Госномер", max_length=100)
    car_region = forms.CharField(label="Регион", max_length=20, required=False)
    car_vin = forms.CharField(label="VIN", max_length=100, required=False)
    car_year = forms.CharField(label="Год выпуска", max_length=10, required=False)

    def cleaned_car_values(self):
        return {
            "model": self.cleaned_data["car_model"].strip(),
            "number": self.cleaned_data["car_number"].strip(),
            "region": self.cleaned_data["car_region"].strip() or None,
            "vin": self.cleaned_data["car_vin"].strip() or None,
            "year": self.cleaned_data["car_year"].strip() or None,
        }
