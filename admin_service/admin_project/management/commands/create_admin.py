from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Create admin user with Admin role'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin')
        parser.add_argument('--email', type=str, default='admin@example.com')
        parser.add_argument('--password', type=str, default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        with transaction.atomic():
            # Создаем суперпользователя
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created admin user: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user {username} already exists'))

            # Добавляем в Admin группу
            admin_group, _ = Group.objects.get_or_create(name='Admin')
            user.groups.add(admin_group)
            
            self.stdout.write(self.style.SUCCESS(f'User {username} added to Admin group'))
            self.stdout.write(self.style.SUCCESS('Login: http://localhost:8001/admin/'))
