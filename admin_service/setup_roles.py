#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Создаем группы
admin_group, created = Group.objects.get_or_create(name='Admin')
operator_group, created = Group.objects.get_or_create(name='Operator')

# Получаем все permissions для наших моделей
content_types = ContentType.objects.filter(
    app_label__in=[
        'admin_users', 'admin_drivers', 'admin_tariffs', 'admin_rides',
        'admin_roles', 'admin_driver_documents', 'admin_chat_messages',
        'admin_commissions', 'admin_transactions', 'admin_ride_status_history'
    ]
)

all_permissions = Permission.objects.filter(content_type__in=content_types)

# Admin получает все права
admin_group.permissions.set(all_permissions)

# Operator получает только view права + некоторые change
view_permissions = all_permissions.filter(codename__startswith='view_')
change_permissions = all_permissions.filter(
    codename__in=[
        'change_user', 'change_driverprofile', 'change_ride',
        'change_transaction', 'change_commission'
    ]
)

operator_permissions = view_permissions | change_permissions
operator_group.permissions.set(operator_permissions)

print('Roles and permissions setup completed')
print(f'Admin group: {admin_group.permissions.count()} permissions')
print(f'Operator group: {operator_group.permissions.count()} permissions')
