from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Назначает или отзывает безопасную роль владельца платформы."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--revoke", action="store_true")

    def handle(self, *args, **options):
        user = get_user_model().objects.filter(username=options["username"]).first()
        if not user: raise CommandError("Пользователь не найден.")
        group, _ = Group.objects.get_or_create(name="platform_owner")
        permissions = Permission.objects.filter(content_type__app_label="platform_admin", codename__in=("access_platform", "view_platform_personal_data", "view_platform_tracker_key", "manage_platform_recommendations"))
        if permissions.count() != 4: raise CommandError("Permissions роли не созданы. Выполните migrate.")
        group.permissions.set(permissions)
        if options["revoke"]:
            user.groups.remove(group); self.stdout.write(self.style.SUCCESS("Роль platform_owner отозвана."))
        else:
            user.groups.add(group); self.stdout.write(self.style.SUCCESS("Роль platform_owner назначена."))

