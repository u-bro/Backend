from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.urls import path

from .policy_views import policy_management_view, policy_preview_view
from admin_drivers.views import moderation_detail, moderation_list
from admin_support.views import conversation_action, unread_count, workspace


class AdminAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].widget.attrs.setdefault("autocomplete", "username")
        if "password" in self.fields:
            self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")


admin.site.login_form = AdminAuthenticationForm

urlpatterns = [
    path('admin/driver-moderation/', admin.site.admin_view(moderation_list), name='driver-moderation-list'),
    path('admin/driver-moderation/<int:profile_id>/', admin.site.admin_view(moderation_detail), name='driver-moderation-detail'),
    path('admin/support/', admin.site.admin_view(workspace), name='support-workspace'),
    path('admin/support/unread-count/', admin.site.admin_view(unread_count), name='support-unread-count'),
    path('admin/support/<int:conversation_id>/', admin.site.admin_view(workspace), name='support-conversation'),
    path('admin/support/<int:conversation_id>/<str:action>/', admin.site.admin_view(conversation_action), name='support-action'),
    path('admin/policies/', admin.site.admin_view(policy_management_view), name='admin-policies'),
    path('admin/policies/<str:policy_key>/preview/', admin.site.admin_view(policy_preview_view), name='admin-policy-preview'),
    path('admin/', admin.site.urls),
]
