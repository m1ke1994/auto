from django.conf import settings
from django.db import migrations


def grant_orders_permissions_to_staff(apps, schema_editor):
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app_label, user_model_name)
    Permission = apps.get_model("auth", "Permission")

    permissions = Permission.objects.filter(content_type__app_label="orders")
    if not permissions.exists():
        return

    for user in User.objects.filter(is_staff=True, is_active=True).iterator():
        user.user_permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(grant_orders_permissions_to_staff, migrations.RunPython.noop),
    ]
