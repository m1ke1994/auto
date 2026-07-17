from django.core.management.base import BaseCommand, CommandError

from apps.sites.models import Site, WebsiteTemplate, WebsiteTemplateCategory
from apps.sites.website_templates import build_site_snapshot


def preview_svg(label, accent, background):
    return (
        "data:image/svg+xml;utf8,"
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 960 540'>"
        f"<rect width='960' height='540' fill='{background}'/>"
        f"<circle cx='760' cy='120' r='180' fill='{accent}' opacity='.18'/>"
        f"<rect x='76' y='84' width='808' height='372' rx='34' fill='white' opacity='.94'/>"
        f"<rect x='128' y='140' width='260' height='22' rx='11' fill='{accent}' opacity='.85'/>"
        f"<rect x='128' y='188' width='540' height='30' rx='15' fill='%2317223B' opacity='.9'/>"
        f"<rect x='128' y='244' width='430' height='18' rx='9' fill='%2364748B' opacity='.55'/>"
        f"<rect x='128' y='284' width='180' height='54' rx='18' fill='{accent}'/>"
        f"<rect x='560' y='262' width='248' height='118' rx='24' fill='{accent}' opacity='.12'/>"
        f"<text x='128' y='410' font-family='Arial' font-size='36' font-weight='700' fill='%2317223B'>{label}</text>"
        "</svg>"
    )


TEMPLATES = [
    {
        "site_slug": "tracknode",
        "category_slug": "business",
        "category_name": "Business",
        "name": "SaaS и цифровой сервис",
        "slug": "saas-digital-service",
        "description": "Шаблон для SaaS, цифрового продукта или технологического сервиса.",
        "preview_image": preview_svg("SaaS analytics", "%236D5DF6", "%23EEF2FF"),
        "sort_order": 10,
    },
    {
        "site_slug": "a-meditation",
        "category_slug": "services",
        "category_name": "Services",
        "name": "Эксперт, практика и консультации",
        "slug": "expert-practice-consulting",
        "description": "Шаблон для эксперта, частной практики, консультаций и персональных услуг.",
        "preview_image": preview_svg("Expert practice", "%2310B981", "%23ECFDF5"),
        "sort_order": 20,
    },
    {
        "site_slug": "novaya-konakova",
        "category_slug": "tourism",
        "category_name": "Tourism",
        "name": "Загородный отдых и мероприятия",
        "slug": "country-retreat-events",
        "description": "Шаблон для загородного отдыха, мероприятий, глэмпинга и туристических проектов.",
        "preview_image": preview_svg("Nature events", "%230F766E", "%23F0FDFA"),
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

        missing = [item["site_slug"] for item in TEMPLATES if not Site.objects.filter(slug=item["site_slug"]).exists()]
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
                "preview_image": item["preview_image"],
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

            template = (
                WebsiteTemplate.objects.filter(slug=item["slug"]).first()
                or WebsiteTemplate.objects.filter(source_site=site).order_by("id").first()
            )
            created = template is None
            if template is None:
                template = WebsiteTemplate(slug=item["slug"])
            else:
                template.slug = item["slug"]
            for field, value in defaults.items():
                setattr(template, field, value)
            template.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"template={template.slug} {'created' if created else 'updated'} source_site={site.slug}"
                )
            )
