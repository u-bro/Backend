from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "is_withdraw", "amount", "created_at")
    list_editable = tuple([f for f in list_display if f != 'id'])
    list_filter = ("is_withdraw", "created_at")
    search_fields = ("user_id",)

    def has_add_permission(self, request):  
        return False

    def has_change_permission(self, request, obj=None):  
        return False

    def has_delete_permission(self, request, obj=None):  
        return False
