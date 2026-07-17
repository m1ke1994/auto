from django.core.management.base import BaseCommand, CommandError

from apps.sites.models import Site, WebsiteTemplate, WebsiteTemplateCategory
from apps.sites.website_templates import build_site_snapshot


TEMPLATES = [
    {
        "site_slug": "tracknode",
        "category_slug": "business",
        "category_name": "Бизнес",
        "name": "SaaS и цифровой сервис",
        "slug": "tracknode-saas-digital-service",
        "description": "Шаблон для SaaS, цифрового продукта или технологического сервиса.",
        "sort_order": 10,
    },
    {
        "site_slug": "leelabird",
        "category_slug": "services",
        "category_name": "Услуги",
        "name": "Эксперт, практика и консультации",
        "slug": "leelabird-expert-consulting",
        "description": "Шаблон для эксперта, частной практики, консультаций и персональных услуг.",
        "sort_order": 20,
    },
    {
        "site_slug": "novaya-konakova",
        "category_slug": "tourism",
        "category_name": "Туризм",
        "name": "Загородный отдых и мероприятия",
        "slug": "novaya-konakova-country-events",
        "description": "Шаблон для загородного отдыха, мероприятий, глэмпинга и туристических проектов.",
        "sort_order": 30,
    },
]


class Command(BaseCommand):
    help = "Register the first public websites as published WebsiteTemplate snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--unpublished", action="store_true")

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        is_published = not bool(options["unpublished"])
        missing = []
        for item in TEMPLATES:
            if not Site.objects.filter(slug=item["site_slug"]).exists():
                missing.append(item["site_slug"])
        if missing:
            raise CommandError(f"Source sites were not found: {', '.join(missing)}")

        for item in TEMPLATES:
            site = Site.objects.get(slug=item["site_slug"])
            category, _ = WebsiteTemplateCategory.objects.get_or_create(
                slug=item["category_slug"],
                defaults={"name": item["category_name"], "sort_order": item["sort_order"], "is_active": True},
            )
            defaults = {
                "name": item["name"],
                "category": category,
                "description": item["description"],
                "preview_image": "",
                "source_site": site,
                "snapshot_config": build_site_snapshot(site),
                "is_published": is_published,
                "is_active": True,
                "is_featured": False,
                "sort_order": item["sort_order"],
            }
            if dry_run:
                self.stdout.write(f"would upsert template={item['slug']} source_site={site.slug}")
                continue
            template, created = WebsiteTemplate.objects.update_or_create(slug=item["slug"], defaults=defaults)
            self.stdout.write(
                self.style.SUCCESS(
                    f"template={template.slug} {'created' if created else 'updated'} source_site={site.slug}"
                )
            )
