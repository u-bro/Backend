from django.contrib import admin

from .models import CommissionPayment


@admin.register(CommissionPayment)
class CommissionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ride_id",
        "user_id",
        "amount",
        "currency",
        "status",
        "is_refund",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "currency", "is_refund", "created_at")
    search_fields = ("ride_id", "user_id", "tochka_operation_id")
    readonly_fields = ("id", "created_at", "updated_at")
