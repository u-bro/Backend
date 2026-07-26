from .models import DriverProfile


def moderation_queue(request):
    try:
        count = DriverProfile.objects.filter(
            status__in=("waiting_register", "waiting_approved", "waiting_moderation")
        ).count()
    except Exception:
        count = 0
    return {"moderation_queue_count": count}
