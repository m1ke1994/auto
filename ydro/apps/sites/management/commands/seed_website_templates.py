from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.sites.models import Site, WebsiteTemplate, WebsiteTemplateCategory
from apps.sites.template_seed_snapshots import (
    A_MEDITATION_BUILDER_KEY,
    ART_STROY_BUILDER_KEY,
    a_meditation_snapshot,
    art_stroy_snapshot,
)
from apps.sites.website_templates import normalize_template_snapshot, validate_template_snapshot


TEMPLATES = [
    {
        "source_slug": "tracknode-template-art-stroy-source",
        "category_slug": "construction",
        "category_name": "Строительство",
        "name": "Art Stroy",
        "slug": "art-stroy",
        "description": "Шаблон для строительных, монтажных и интерьерных компаний на базе дизайна Art Stroy.",
        "preview_image": "/template-previews/art-stroy.svg",
        "builder_template_key": ART_STROY_BUILDER_KEY,
        "snapshot_factory": art_stroy_snapshot,
        "sort_order": 10,
    },
    {
        "source_slug": "tracknode-template-a-meditation-source",
        "category_slug": "tourism",
        "category_name": "Туризм",
        "name": "A Meditation",
        "slug": "a-meditation",
        "description": "Шаблон для ретритов, медитаций и авторских практик на базе дизайна leelabird.ru.",
        "preview_image": "/template-previews/a-meditation.svg",
        "builder_template_key": A_MEDITATION_BUILDER_KEY,
        "snapshot_factory": a_meditation_snapshot,
        "sort_order": 20,
    },
]


class Command(BaseCommand):
    help = "Register published WebsiteTemplate snapshots for generated sites."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--unpublished", action="store_true")

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        is_published = not bool(options["unpublished"])
        source_owner = None if dry_run else self._source_owner()

        for item in TEMPLATES:
            snapshot = item["snapshot_factory"]()
            source_site = self._upsert_source_site(item, source_owner, snapshot, dry_run=dry_run)
            if dry_run:
                category = WebsiteTemplateCategory(
                    slug=item["category_slug"],
                    name=item["category_name"],
                    sort_order=item["sort_order"],
                    is_active=True,
                )
            else:
                category, _ = WebsiteTemplateCategory.objects.update_or_create(
                    slug=item["category_slug"],
                    defaults={"name": item["category_name"], "sort_order": item["sort_order"], "is_active": True},
                )
            normalized_snapshot = normalize_template_snapshot(
                WebsiteTemplate(slug=item["slug"], source_site=source_site),
                snapshot,
            )
            validate_template_snapshot(normalized_snapshot)
            defaults = {
                "name": item["name"],
                "category": category,
                "description": item["description"],
                "preview_image": item["preview_image"],
                "source_site": source_site,
                "snapshot_config": normalized_snapshot,
                "is_published": is_published,
                "is_active": True,
                "is_featured": False,
                "sort_order": item["sort_order"],
            }
            if dry_run:
                self.stdout.write(f"would upsert template={item['slug']} source_site={source_site.slug}")
                continue

            template, created = WebsiteTemplate.objects.update_or_create(slug=item["slug"], defaults=defaults)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{template.name}: {'created' if created else 'updated'} "
                    f"key={item['builder_template_key']} category={item['category_slug']}"
                )
            )

    def _source_owner(self):
        user_model = get_user_model()
        owner, _ = user_model.objects.get_or_create(
            username="tracknode-template-source",
            defaults={"email": "templates@tracknode.local", "is_active": False},
        )
        if owner.has_usable_password():
            owner.set_unusable_password()
            owner.save(update_fields=["password"])
        return owner

    def _upsert_source_site(self, item, owner, snapshot, *, dry_run):
        site_defaults = {
            "name": item["name"],
            "domain": "",
            "source": Site.Source.TEMPLATE,
            "render_mode": Site.RenderMode.BUILDER,
            "status": Site.Status.DRAFT,
            "generation_status": Site.GenerationStatus.COMPLETED,
            "generation_progress": 100,
            "generation_error": "",
            "design_preset": snapshot["site"]["design_preset"],
            "builder_template_key": item["builder_template_key"],
            "builder_config": snapshot["site"]["builder_config"],
            "is_active": False,
            "send_to_telegram": False,
            "telegram_chat_id": None,
            "telegram_connected_at": None,
            "seo": {},
        }
        if dry_run:
            site = Site.objects.filter(slug=item["source_slug"]).first()
            return site or Site(slug=item["source_slug"], owner=owner, **site_defaults)
        site_defaults["owner"] = owner
        site, _ = Site.objects.update_or_create(slug=item["source_slug"], defaults=site_defaults)
        return site
