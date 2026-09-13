from django.urls import reverse

from .admin_stats import entity_stats, get_entity_spec


class EntityStatsAdminMixin:
    change_list_template = "admin/entity_stats_change_list.html"

    def changelist_view(self, request, extra_context=None):
        spec = get_entity_spec(self.model._meta.app_label, self.model._meta.model_name)
        context = dict(extra_context or {})
        if spec is not None:
            context.update(
                entity_stats=entity_stats(spec),
                entity_stats_url=reverse(
                    "admin-entity-stats",
                    args=(spec.app_label, spec.model_name),
                ),
            )
        return super().changelist_view(request, extra_context=context)
