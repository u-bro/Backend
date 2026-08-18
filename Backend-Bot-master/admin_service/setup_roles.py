#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

admin_group, created = Group.objects.get_or_create(name='Admin')
operator_group, created = Group.objects.get_or_create(name='Operator')

content_types = ContentType.objects.filter(
    app_label__in=[
        'admin_users', 'admin_drivers', 'admin_rides',
        'admin_roles', 'admin_driver_documents', 'admin_chat_messages',
        'admin_commissions', 'admin_commission_payments',
        'admin_ride_status_history', 'admin_cars', 'admin_car_photos',
        'admin_driver_locations', 'admin_ride_drivers_requests'
    ]
)

all_permissions = Permission.objects.filter(content_type__in=content_types)
auth_view_permissions = Permission.objects.filter(
    content_type__app_label='auth',
    codename__in=['view_user', 'view_group'],
)
admin_permissions = all_permissions | auth_view_permissions

admin_group.permissions.set(admin_permissions)

view_permissions = all_permissions.filter(codename__startswith='view_') | auth_view_permissions
change_permissions = all_permissions.filter(
    codename__in=[
        'change_user', 'change_driverprofile', 'change_ride',
        'change_commission'
    ]
)

operator_permissions = view_permissions | change_permissions
operator_group.permissions.set(operator_permissions)

print('Roles and permissions setup completed')
print(f'Admin group: {admin_group.permissions.count()} permissions')
print(f'Operator group: {operator_group.permissions.count()} permissions')
