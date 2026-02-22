from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "ride_id", "user_id", "amount", "currency", "status", "is_refund", "created_at")
    list_filter = ("status", "is_refund", "created_at")
    search_fields = ("user_id", "ride_id")
    list_per_page = 25

    def has_add_permission(self, request):  
        return False

    def has_change_permission(self, request, obj=None):  
        return False

    def has_delete_permission(self, request, obj=None):  
        return False
