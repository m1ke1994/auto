import os

from django.db import migrations


LOCAL_DOMAINS = {
    "",
    "localhost",
    "localhost:3000",
    "localhost:5173",
    "127.0.0.1",
    "127.0.0.1:3000",
    "127.0.0.1:5173",
}

def update_a_meditation_public_domain(apps, schema_editor):
    public_domain = os.getenv("PUBLIC_SITE_DEFAULT_DOMAIN", "").strip()
    if not public_domain:
        return

    Site = apps.get_model("sites", "Site")
    site = Site.objects.filter(slug="a-meditation").first()
    if site is None or site.domain not in LOCAL_DOMAINS:
        return

    site.domain = public_domain
    site.save(update_fields=["domain", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0011_sync_a_meditation_sections"),
    ]

    operations = [
        migrations.RunPython(update_a_meditation_public_domain, migrations.RunPython.noop),
    ]
