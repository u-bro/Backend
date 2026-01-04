#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.db import transaction

# Создаем суперпользователя (без печати пароля)
username = os.getenv('ADMIN_USERNAME', 'admin')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin12345')  # Рекомендовано задавать через окружение

with transaction.atomic():
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        if password:
            user.set_password(password)
            user.save()
            print(f'Created admin user: {username} (password set from ADMIN_PASSWORD env var)')
        else:
            # Создали без заданного пароля — админ должен установить пароль через manage.py changepassword
            user.save()
            print(f'Created admin user: {username} (no password set). Run `manage.py changepassword {username}` to set a password.')
    else:
        print(f'Admin user {username} already exists')

    # Добавляем в Admin группу
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    user.groups.add(admin_group)
    
    print(f'User {username} added to Admin group')
    print('Login: http://localhost:8001/admin/')
