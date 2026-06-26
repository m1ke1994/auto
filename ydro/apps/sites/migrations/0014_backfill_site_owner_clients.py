import secrets
import uuid

from django.db import migrations


def _generate_unique_api_key(Client):
    while True:
        api_key = secrets.token_urlsafe(32)
        if not Client.objects.filter(api_key=api_key).exists():
            return api_key


def _client_name_for_site(site):
    for value in (
        getattr(site, "name", ""),
        getattr(site, "domain", ""),
        getattr(site.owner, "email", ""),
        getattr(site.owner, "username", ""),
    ):
        value = str(value or "").strip()
        if value:
            return value
    return "Site owner"


def backfill_site_owner_clients(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Client = apps.get_model("clients", "Client")

    existing_owner_ids = set(Client.objects.values_list("owner_id", flat=True))
    created_owner_ids = set()

    for site in Site.objects.select_related("owner").filter(is_active=True).order_by("owner_id", "id"):
        owner_id = site.owner_id
        if owner_id in existing_owner_ids or owner_id in created_owner_ids:
            continue

        Client.objects.create(
            owner_id=owner_id,
            name=_client_name_for_site(site),
            uuid=uuid.uuid4(),
            api_key=_generate_unique_api_key(Client),
            telegram_chat_id=None,
            send_to_telegram=False,
            is_active=True,
        )
        created_owner_ids.add(owner_id)


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0006_alter_client_options_alter_client_api_key_and_more"),
        ("sites", "0013_add_novaya_konakova_section_schemas"),
    ]

    operations = [
        migrations.RunPython(backfill_site_owner_clients, migrations.RunPython.noop),
    ]
