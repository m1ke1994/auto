from copy import deepcopy

from django.db import migrations


NEW_BRAND = "Leelabird"
DEFAULT_TITLE = "Leelabird — трансформационная игра Лила и практики медитации"
DEFAULT_DESCRIPTION = (
    "Индивидуальные сессии, трансформационная игра Лила, медитации и практики "
    "осознанного развития с Ольгой."
)
DEFAULT_IMAGE = "/images/Lila_Olga_2.2.poster.jpg"
OLD_BRANDS = (
    "A" + " Meditation",
    "A" + " meditation",
    "a" + " meditation",
    "A" + "Meditation",
)


def _replace_legacy_brand(value):
    if isinstance(value, str):
        next_value = value
        for old_brand in OLD_BRANDS:
            next_value = next_value.replace(old_brand, NEW_BRAND)
        return next_value
    if isinstance(value, list):
        return [_replace_legacy_brand(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_legacy_brand(item) for key, item in value.items()}
    return value


def _contains_legacy_brand(value):
    return isinstance(value, str) and any(old_brand.lower() in value.lower() for old_brand in OLD_BRANDS)


def _should_replace_description(value):
    if not isinstance(value, str) or not value.strip():
        return True
    lowered = value.lower()
    return _contains_legacy_brand(value) or "демо-сайт" in lowered


def rebrand_public_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    SiteSection = apps.get_model("sites", "SiteSection")
    Client = apps.get_model("clients", "Client")

    site = Site.objects.filter(slug="a-meditation").first()
    if site is None:
        return

    seo = deepcopy(site.seo if isinstance(site.seo, dict) else {})
    seo = _replace_legacy_brand(seo)
    if not seo.get("title") or _contains_legacy_brand(seo.get("title")):
        seo["title"] = DEFAULT_TITLE
    if _should_replace_description(seo.get("description")):
        seo["description"] = DEFAULT_DESCRIPTION
    if not seo.get("site_name") or _contains_legacy_brand(seo.get("site_name")):
        seo["site_name"] = NEW_BRAND
    seo.setdefault("image", DEFAULT_IMAGE)

    site.name = NEW_BRAND
    site.seo = seo
    site.save(update_fields=["name", "seo", "updated_at"])

    for section in SiteSection.objects.filter(site=site):
        section.content = _replace_legacy_brand(section.content if isinstance(section.content, dict) else {})
        section.seo = _replace_legacy_brand(section.seo if isinstance(section.seo, dict) else {})
        if isinstance(section.seo, dict) and _contains_legacy_brand(section.seo.get("title")):
            section.seo["title"] = _replace_legacy_brand(section.seo["title"])
        section.save(update_fields=["content", "seo", "updated_at"])

    for client in Client.objects.filter(owner_id=site.owner_id):
        if _contains_legacy_brand(client.name):
            client.name = _replace_legacy_brand(client.name)
            client.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0014_backfill_site_owner_clients"),
    ]

    operations = [
        migrations.RunPython(rebrand_public_site, migrations.RunPython.noop),
    ]
