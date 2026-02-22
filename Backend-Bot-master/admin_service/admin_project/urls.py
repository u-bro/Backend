from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.urls import path


class AdminAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].widget.attrs.setdefault("autocomplete", "username")
        if "password" in self.fields:
            self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")


admin.site.login_form = AdminAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
]
