from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from utils.policy_storage import policy_storage


POLICY_TYPES = (
    ("privacy-policy", "Политика обработки персональных данных"),
    ("confidentiality-policy", "Политика конфиденциальности данных"),
    ("terms-of-service", "Пользовательское соглашение"),
    ("public-offer", "Оферта"),
)
ALLOWED_POLICY_TYPES = {key for key, _ in POLICY_TYPES}


def _validate_policy_key(policy_key: str) -> None:
    if policy_key not in ALLOWED_POLICY_TYPES:
        raise Http404("Policy not found")


def _has_policy_access(user) -> bool:
    return user.is_superuser or user.groups.filter(name="Admin").exists()


@staff_member_required
def policy_management_view(request):
    if not _has_policy_access(request.user):
        messages.error(request, "Недостаточно прав для управления политиками.")
        return HttpResponseRedirect(reverse("admin:index"))

    if request.method == "POST":
        policy_key = request.POST.get("policy_key", "")
        _validate_policy_key(policy_key)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            messages.error(request, "Выберите PDF-файл для загрузки.")
            return HttpResponseRedirect(reverse("admin-policies"))

        content_type = uploaded_file.content_type or "application/octet-stream"
        if content_type != "application/pdf" and not uploaded_file.name.lower().endswith(".pdf"):
            messages.error(request, "Допускаются только PDF-файлы.")
            return HttpResponseRedirect(reverse("admin-policies"))

        try:
            policy_storage.upload(
                policy_key=policy_key,
                content=uploaded_file.read(),
                content_type="application/pdf",
            )
            messages.success(request, f"Политика '{policy_key}' обновлена.")
        except Exception:
            messages.error(request, f"Не удалось обновить политику '{policy_key}'.")

        return HttpResponseRedirect(reverse("admin-policies"))

    policy_items = [
        {
            "key": key,
            "label": label,
            "preview_url": reverse("admin-policy-preview", args=[key]),
        }
        for key, label in POLICY_TYPES
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Политики",
        "policy_items": policy_items,
    }
    return render(request, "admin/policies.html", context)


@staff_member_required
@xframe_options_sameorigin
def policy_preview_view(request, policy_key: str):
    if not _has_policy_access(request.user):
        raise Http404("Policy not found")

    _validate_policy_key(policy_key)

    try:
        content, content_type, content_disposition = policy_storage.get(policy_key)
    except FileNotFoundError:
        raise Http404("Policy not found")
    except Exception:
        return HttpResponse(status=502)

    return HttpResponse(
        content,
        content_type=content_type,
        headers={"Content-Disposition": content_disposition},
    )
