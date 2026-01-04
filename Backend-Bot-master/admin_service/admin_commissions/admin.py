from django.contrib import admin

from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "percentage",
        "fixed_amount",
        "currency",
        "valid_from",
        "valid_to",
        "created_at",
    )
    list_editable = ()  # Read-only: has_change_permission=False
    list_filter = ("valid_from", "valid_to", "created_at")
    search_fields = ("name", "currency")

    def has_add_permission(self, request):  # type: ignore[override]
        return request.user.groups.filter(name='Admin').exists()

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name='Admin').exists()

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return request.user.groups.filter(name='Admin').exists()
