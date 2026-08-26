from django.contrib import admin, messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods

from .client import PushAPIError, PushAPITimeout, send_push
from .forms import PushNotificationForm


def can_send_push(user):
    return bool(
        user.is_active
        and user.is_staff
        and (user.is_superuser or user.groups.filter(name="Admin").exists())
    )


def operator_name(user):
    return user.get_full_name().strip() or user.get_username()


@require_http_methods(["GET", "POST"])
def send_push_view(request):
    if not can_send_push(request.user):
        raise Http404()

    form = PushNotificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        selected_user = form.cleaned_data["user"]
        payload = {
            "audience": form.cleaned_data["audience"],
            "user_id": selected_user.id if selected_user else None,
            "title": form.cleaned_data["title"],
            "body": form.cleaned_data["body"],
            "operator_id": request.user.id,
            "operator_name": operator_name(request.user),
        }
        try:
            result = send_push(payload)
        except PushAPITimeout as exc:
            messages.warning(request, str(exc))
        except PushAPIError as exc:
            messages.error(request, str(exc))
        else:
            history_url = reverse("admin:admin_push_notifications_adminpushnotification_change", args=[result["history_id"]])
            message = format_html(
                "Push обработан со статусом {}: успешно {}, ошибок {}, токенов {}. <a href=\"{}\">Открыть запись истории</a>.",
                result["status"], result["success_count"], result["failure_count"], result["attempted_token_count"], history_url,
            )
            if result["status"] == "sent":
                messages.success(request, message)
            else:
                messages.warning(request, format_html("{} Не повторяйте отправку без проверки истории.", message))
        return redirect("admin-push-send")

    context = {
        **admin.site.each_context(request),
        "title": "Отправить push-уведомление",
        "form": form,
        "history_url": reverse("admin:admin_push_notifications_adminpushnotification_changelist"),
    }
    return render(request, "admin_push_notifications/send.html", context)
