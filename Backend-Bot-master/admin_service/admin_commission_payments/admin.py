from django.contrib import admin

from .models import CommissionPayment
from utils.admin_links import ride_link, user_link
from utils.admin_stats_admin import EntityStatsAdminMixin


@admin.register(CommissionPayment)
class CommissionPaymentAdmin(EntityStatsAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id_link",
        "user_id_link",
        "amount",
        "currency",
        "status",
        "is_refund",
        "paid_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "is_refund", "paid_at", "created_at")
    search_fields = ("ride_id", "user_id", "payment_id")
    list_per_page = 25
    readonly_fields = ("ride_id_link", "user_id_link")

    @admin.display(description="Номер поездки", ordering="ride_id")
    def ride_id_link(self, obj):
        return ride_link(getattr(obj, "ride_id", None))

    @admin.display(description="Номер пользователя", ordering="user_id")
    def user_id_link(self, obj):
        return user_link(getattr(obj, "user_id", None))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
