from copy import deepcopy

from django.db import migrations


def add_novaya_konakova_section_schemas(apps, schema_editor):
    from apps.sites.volga_site import (
        VOLGA_SECTION_SEEDS,
        VOLGA_SITE_SLUG,
        get_site_specific_schema_key,
    )

    SectionSchema = apps.get_model("sites", "SectionSchema")

    for seed in VOLGA_SECTION_SEEDS:
        SectionSchema.objects.update_or_create(
            section_key=get_site_specific_schema_key(seed["key"], VOLGA_SITE_SLUG),
            defaults={
                "title": seed["title"],
                "schema": deepcopy(seed["schema"]),
                "description": f"Поля раздела «{seed['title']}» сайта Новая Конакова",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0012_update_a_meditation_public_domain"),
    ]

    operations = [
        migrations.RunPython(add_novaya_konakova_section_schemas, migrations.RunPython.noop),
    ]
