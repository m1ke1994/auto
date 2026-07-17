from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.sites.models import Site, WebsiteTemplate, WebsiteTemplateCategory
from apps.sites.website_templates import build_site_snapshot


class Command(BaseCommand):
    help = "Register an existing Site as a source for the site template catalog."

    def add_arguments(self, parser):
        parser.add_argument("--site-slug", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--category", required=True)
        parser.add_argument("--template-slug", default="")
        parser.add_argument("--description", default="")
        parser.add_argument("--preview-image", default="")
        parser.add_argument("--featured", action="store_true")
        parser.add_argument("--published", action="store_true")
        parser.add_argument("--sort-order", type=int, default=100)

    def handle(self, *args, **options):
        site = Site.objects.filter(slug=options["site_slug"]).first()
        if site is None:
            raise CommandError(f"Site with slug={options['site_slug']} was not found.")

        category = WebsiteTemplateCategory.objects.filter(slug=options["category"], is_active=True).first()
        if category is None:
            raise CommandError(f"Active template category slug={options['category']} was not found.")

        template_slug = options["template_slug"] or slugify(options["name"])
        if not template_slug:
            raise CommandError("Template slug is empty.")

        template, created = WebsiteTemplate.objects.update_or_create(
            slug=template_slug,
            defaults={
                "name": options["name"],
                "category": category,
                "description": options["description"],
                "preview_image": options["preview_image"],
                "source_site": site,
                "snapshot_config": build_site_snapshot(site),
                "is_published": bool(options["published"]),
                "is_active": True,
                "is_featured": bool(options["featured"]),
                "sort_order": options["sort_order"],
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"template={template.slug} {'created' if created else 'updated'} source_site={site.slug}"
            )
        )
