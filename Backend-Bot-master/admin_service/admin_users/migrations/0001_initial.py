from django.db import migrations, transaction
import os
from django.utils import timezone


def create_admin(apps, schema_editor):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    User = get_user_model()

    first_name = os.environ.get('ADMIN_USERNAME', 'admin')
    if not first_name:
        first_name = 'admin'
    password = os.getenv('ADMIN_PASSWORD', 'NewStrongPass123')

    with transaction.atomic():
        try:
            user = User.objects.get(username=first_name)
            created = False
        except User.DoesNotExist:
            user = User(
                username=first_name,
                first_name=first_name,
                is_staff=True,
                is_superuser=True,
                last_login=timezone.now(),
            )
            user.save()
            created = True

        if created:
            if password:
                user.set_password(password)
                user.save()
                print(f'Created admin user: {first_name} (password set from ADMIN_PASSWORD env var)')
            else:
                print(f'Created admin user: {first_name} (no password set). Run `manage.py changepassword {first_name}` to set a password.')
        else:
            if password:
                user.set_password(password)
                user.last_login = timezone.now()
                user.save()
                print(f'Updated password for existing admin user: {first_name}')
            else:
                user.last_login = timezone.now()
                user.save()
                print(f'Admin user {first_name} already exists')

        admin_group, _ = Group.objects.get_or_create(name='Admin')
        user.groups.add(admin_group)
        print(f'User {first_name} added to Admin group')
        print('Login: http://localhost:8001/admin/')


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_admin, noop_reverse),
    ]
