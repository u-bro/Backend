from django import template

register = template.Library()

from utils.moderation_labels import DOCUMENT_LABELS, STATUS_LABELS, REASON_LABELS


@register.filter
def document_label(value):
    return DOCUMENT_LABELS.get(value, value or "Документ без названия")


@register.filter
def car_photo_label(value):
    return DOCUMENT_LABELS.get(f"CAR_PHOTO_{value}", DOCUMENT_LABELS.get(value, value or "Фото автомобиля"))


@register.filter
def moderation_status(value):
    return STATUS_LABELS.get(value, value or "Статус не указан")


@register.filter
def moderation_reason(reason):
    # Keep custom reasons visible; translate seeded reasons without changing DB codes.
    return REASON_LABELS.get(reason.code, reason.message or "Причина не указана")
