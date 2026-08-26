from django import forms

from admin_users.models import User


class PushNotificationForm(forms.Form):
    audience = forms.ChoiceField(
        label="Получатели",
        choices=(("user", "Один пользователь"), ("all", "Все аккаунты с push-токеном")),
        widget=forms.RadioSelect,
    )
    user = forms.ModelChoiceField(
        label="Пользователь",
        queryset=User.objects.all(),
        required=False,
        widget=forms.HiddenInput,
    )
    title = forms.CharField(label="Заголовок", max_length=255)
    body = forms.CharField(label="Текст", max_length=2000, widget=forms.Textarea(attrs={"rows": 6}))
    confirm_all = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def clean(self):
        cleaned = super().clean()
        audience = cleaned.get("audience")
        user = cleaned.get("user")
        if audience == "user" and user is None:
            self.add_error("user", "Выберите пользователя.")
        if audience == "all" and user is not None:
            cleaned["user"] = None
        if audience == "all" and not cleaned.get("confirm_all"):
            self.add_error("confirm_all", "Подтвердите массовую отправку.")
        return cleaned
