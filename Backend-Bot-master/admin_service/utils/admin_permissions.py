def has_service_permission(user, permission, legacy_groups=()):
    """Honor explicit permissions while retaining access for existing roles."""
    return bool(
        user.is_active
        and user.is_staff
        and (
            user.is_superuser
            or user.groups.filter(name__in=legacy_groups).exists()
            or user.has_perm(permission)
        )
    )


def all_service_permissions():
    """All installed service rights; administrator accounts remain read-only."""
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q

    policy_permission, _ = Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Group),
        codename="manage_service_policies",
        defaults={"name": "Может управлять политиками сервиса"},
    )
    return Permission.objects.filter(
        ~Q(content_type__app_label="auth")
        | Q(content_type__app_label="auth", codename="view_user")
        | Q(pk=policy_permission.pk)
    )
