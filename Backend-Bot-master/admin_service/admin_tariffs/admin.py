from django.contrib import admin
from django.contrib import messages
from django import forms

from .models import TariffPlan


class TariffPlanForm(forms.ModelForm):
    class Meta:
        model = TariffPlan
        fields = "__all__"


@admin.register(TariffPlan)
class TariffPlanAdmin(admin.ModelAdmin):
    form = TariffPlanForm
    list_display = (
        "id",
        "name",
        "effective_from",
        "effective_to",
        "base_fare",
        "rate_per_meter",
        "multiplier",
        "commission_percentage",
        "created_at",
        "updated_at",
    )
    list_filter = ("effective_from", "effective_to")
    search_fields = ("name",)

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
