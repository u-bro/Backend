from django.db import migrations, transaction
import os

def create_admin(apps, schema_editor):
    # Create or update a superuser and ensure 'Admin' group exists
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.utils import timezone  # Импорт внутри функции для избежания проблем при сборке контейнера

    User = get_user_model()

    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'NewStrongPass123')

    with transaction.atomic():
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'last_login': timezone.now(),  # <-- добавлено!
            }
        )

        if created:
            if password:
                user.set_password(password)
                user.save()
                print(f'Created admin user: {username} (password set from ADMIN_PASSWORD env var)')
            else:
                user.save()
                print(f'Created admin user: {username} (no password set). Run `manage.py changepassword {username}` to set a password.')
        else:
            # If user exists and ADMIN_PASSWORD provided, reset it
            if password:
                user.set_password(password)
                user.save()
                print(f'Updated password for existing admin user: {username}')
            else:
                print(f'Admin user {username} already exists')

        # Ensure Admin group exists and assign
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        user.groups.add(admin_group)
        print(f'User {username} added to Admin group')
        print('Login: http://localhost:8001/admin/')

def noop_reverse(apps, schema_editor):
    # Do not remove admin on reverse
    return

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_admin, noop_reverse),
    ]