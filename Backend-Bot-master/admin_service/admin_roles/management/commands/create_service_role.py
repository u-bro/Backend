from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from utils.admin_permissions import all_service_permissions


class Command(BaseCommand):
    help = "Create a staff role with service access and read-only administrators."

    def add_arguments(self, parser):
        parser.add_argument("--name", default="Управляющий сервисом")

    @transaction.atomic
    def handle(self, *args, **options):
        name = options["name"].strip()
        if not name:
            raise CommandError("Role name must not be empty")
        role, created = Group.objects.get_or_create(name=name)
        if not created:
            raise CommandError("Role already exists; edit its permissions in the admin panel")
        role.permissions.set(all_service_permissions())
        self.stdout.write(self.style.SUCCESS(f"Created role: {role.name}"))
