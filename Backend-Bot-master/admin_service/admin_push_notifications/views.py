import re

from django.contrib import admin, messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods

from admin_users.models import User

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


def user_label(user):
    name = " ".join(part for part in (user.last_name, user.first_name, user.middle_name) if part)
    details = " · ".join(part for part in (name, user.phone, user.email) if part)
    return f"#{user.id} · {details}" if details else f"#{user.id}"


@require_http_methods(["GET"])
def user_search(request):
    if not can_send_push(request.user):
        raise Http404()

    query = request.GET.get("q", "").strip()
    if len(query) < 2 and not query.isdigit():
        return JsonResponse({"results": []})

    filters = (
        Q(phone__icontains=query)
        | Q(email__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(middle_name__icontains=query)
    )
    terms = query.split()
    if len(terms) > 1:
        name_filters = Q()
        for term in terms:
            name_filters &= Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(middle_name__icontains=term)
        filters |= name_filters

    numeric = query.lstrip("#")
    if numeric.isdigit():
        filters |= Q(id=int(numeric))
    normalized_phone = re.sub(r"\D", "", query)
    if normalized_phone:
        filters |= Q(phone__iregex=rf"[^0-9]*{'[^0-9]*'.join(normalized_phone)}[^0-9]*")

    users = User.objects.filter(filters).order_by("id")[:20]
    return JsonResponse({
        "results": [
            {
                "id": user.id,
                "label": user_label(user),
                "is_active": user.is_active,
            }
            for user in users
        ]
    })


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
            if exc.code == "ADMIN_PUSH_DUPLICATE_RECENT" and exc.history_id:
                history_url = reverse(
                    "admin:admin_push_notifications_adminpushnotification_change",
                    args=[exc.history_id],
                )
                messages.error(
                    request,
                    format_html(
                        '{} <a href="{}">Открыть предыдущую отправку #{}</a>.',
                        str(exc), history_url, exc.history_id,
                    ),
                )
            else:
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

    selected_user = None
    selected_user_id = request.POST.get("user") if request.method == "POST" else None
    if selected_user_id and selected_user_id.isdigit():
        selected_user = User.objects.filter(id=int(selected_user_id)).first()

    context = {
        **admin.site.each_context(request),
        "title": "Отправить push-уведомление",
        "form": form,
        "history_url": reverse("admin:admin_push_notifications_adminpushnotification_changelist"),
        "user_search_url": reverse("admin-push-user-search"),
        "selected_user_label": user_label(selected_user) if selected_user else None,
        "selected_user_is_active": selected_user.is_active if selected_user else None,
    }
    return render(request, "admin_push_notifications/send.html", context)
