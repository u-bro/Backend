import uuid

from django.contrib import admin, messages
from django.db.models import BigIntegerField, Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from utils.admin_links import safe_external_url

from .client import SupportAPIError, support_action
from .models import SupportConversation, SupportMessage


def can_access_support(user):
    return bool(
        user.is_active
        and user.is_staff
        and (user.is_superuser or user.groups.filter(name__in=("Admin", "Operator")).exists())
    )


def can_change_support(user):
    return can_access_support(user) and (user.is_superuser or user.has_perm("admin_support.change_supportconversation"))


def _require_access(request):
    if not can_access_support(request.user):
        raise Http404()


def with_unread(queryset):
    read_marker = Coalesce(
        F("last_read_message_id"),
        Value(0),
        output_field=BigIntegerField(),
    )
    return queryset.annotate(
        unread_count=Count(
            "support_messages",
            filter=Q(
                support_messages__sender_type="USER",
                support_messages__id__gt=read_marker,
            ),
            distinct=True,
        )
    )


def operator_name(user):
    return user.get_full_name().strip() or user.get_username()


@require_GET
def workspace(request, conversation_id=None):
    _require_access(request)
    status = request.GET.get("status", "OPEN").upper()
    query = request.GET.get("q", "").strip()
    unread_only = request.GET.get("unread") == "1"

    latest = SupportMessage.objects.filter(conversation_id=OuterRef("pk")).order_by("-created_at", "-id")
    conversations = with_unread(SupportConversation.objects.select_related("user")).annotate(
        latest_text=Subquery(latest.values("text")[:1]),
        latest_sender=Subquery(latest.values("sender_type")[:1]),
        latest_created_at=Subquery(latest.values("created_at")[:1]),
    )
    if status in ("OPEN", "CLOSED"):
        conversations = conversations.filter(status=status)
    if unread_only:
        conversations = conversations.filter(unread_count__gt=0)
    if query:
        numeric = query.lstrip("#")
        if numeric.isdigit():
            conversations = conversations.filter(Q(id=int(numeric)) | Q(max_user_id=int(numeric)))
        else:
            search = Q(user__phone__icontains=query) | Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
            conversations = conversations.filter(search)
    conversations = list(conversations.order_by("-updated_at", "-id")[:100])

    selected = None
    selected_messages = []
    if conversation_id is not None:
        selected = get_object_or_404(
            with_unread(SupportConversation.objects.select_related("user")),
            pk=conversation_id,
        )
        selected_messages = list(selected.support_messages.prefetch_related("attachments").all())
        selected.visible_last_inbound_id = max(
            (item.id for item in selected_messages if item.sender_type == "USER"),
            default=None,
        )
        for item in selected_messages:
            for attachment in item.attachments.all():
                attachment.safe_url = safe_external_url(attachment.provider_url)

    context = {
        **admin.site.each_context(request),
        "title": "Поддержка",
        "conversations": conversations,
        "selected": selected,
        "selected_messages": selected_messages,
        "selected_status": status,
        "search_query": query,
        "unread_only": unread_only,
    }
    return render(request, "admin_support/workspace.html", context)


@require_POST
def conversation_action(request, conversation_id, action):
    _require_access(request)
    if not can_change_support(request.user):
        raise Http404()
    conversation = get_object_or_404(SupportConversation, pk=conversation_id)
    payload = None
    if action == "reply":
        if conversation.status != "OPEN":
            messages.error(request, "Закрытый диалог нужно сначала открыть.")
            return redirect("support-conversation", conversation_id=conversation_id)
        text = request.POST.get("text", "").strip()
        if not text or len(text) > 4000:
            messages.error(request, "Ответ должен содержать от 1 до 4000 символов.")
            return redirect("support-conversation", conversation_id=conversation_id)
        payload = {"text": text, "idempotency_key": f"django-{uuid.uuid4().hex}"}
        api_action = "messages"
    elif action == "retry":
        message_id = request.POST.get("message_id", "")
        failed_message = get_object_or_404(
            conversation.support_messages,
            pk=message_id,
            sender_type="OPERATOR",
            delivery_status="FAILED",
        )
        if not failed_message.text or not failed_message.idempotency_key:
            messages.error(request, "Это сообщение нельзя отправить повторно.")
            return redirect("support-conversation", conversation_id=conversation_id)
        payload = {
            "text": failed_message.text,
            "idempotency_key": failed_message.idempotency_key,
        }
        api_action = "messages"
    elif action == "read":
        marker = request.POST.get("up_to_message_id", "")
        latest_user_message = conversation.support_messages.filter(id=marker, sender_type="USER").first()
        if latest_user_message is None:
            messages.info(request, "Нет входящих сообщений для отметки.")
            return redirect("support-conversation", conversation_id=conversation_id)
        payload = {"up_to_message_id": latest_user_message.id}
        api_action = "read"
    elif action in ("close", "reopen"):
        api_action = action
    else:
        raise Http404()

    try:
        result = support_action(conversation_id, api_action, operator_name(request.user), payload)
        if result.get("delivery_status") == "FAILED":
            messages.error(request, "Ответ сохранен, но не доставлен в MAX. Используйте «Повторить».")
        else:
            messages.success(request, "Действие выполнено.")
    except SupportAPIError as exc:
        messages.error(request, str(exc))
    target_status = result.get("status", conversation.status) if "result" in locals() else conversation.status
    return redirect(f"{reverse('support-conversation', args=[conversation_id])}?status={target_status}")


@require_GET
def unread_count(request):
    _require_access(request)
    read_marker = Coalesce(
        F("conversation__last_read_message_id"),
        Value(0),
        output_field=BigIntegerField(),
    )
    unread = SupportMessage.objects.filter(
        sender_type="USER",
        id__gt=read_marker,
    )
    return JsonResponse({
        "unread_messages": unread.count(),
        "unread_conversations": unread.values("conversation_id").distinct().count(),
    })
