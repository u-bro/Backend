from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create admin roles and permissions'

    def handle(self, *args, **options):
        admin_group, created = Group.objects.get_or_create(name='Admin')
        operator_group, created = Group.objects.get_or_create(name='Operator')

        content_types = ContentType.objects.filter(
            app_label__in=[
                'admin_users', 'admin_drivers', 'admin_tariffs', 'admin_rides',
                'admin_roles', 'admin_driver_documents', 'admin_chat_messages',
                'admin_commissions', 'admin_ride_status_history'
            ]
        )
        
        all_permissions = Permission.objects.filter(content_type__in=content_types)

        admin_group.permissions.set(all_permissions)

        view_permissions = all_permissions.filter(codename__startswith='view_')
        change_permissions = all_permissions.filter(
            codename__in=[
                'change_user', 'change_driverprofile', 'change_ride',
                'change_commission'
            ]
        )
        
        operator_permissions = view_permissions | change_permissions
        operator_group.permissions.set(operator_permissions)

        self.stdout.write(self.style.SUCCESS('Roles and permissions created successfully'))
