from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.sites.models import Site, WebsiteTemplate
from apps.sites.website_templates import build_site_snapshot, normalize_template_snapshot, validate_template_snapshot


class Command(BaseCommand):
    help = "Rebuild one WebsiteTemplate snapshot from its source Site."

    def add_arguments(self, parser):
        parser.add_argument("--template-id", type=int, required=True)
        parser.add_argument("--source-site-id", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        template = WebsiteTemplate.objects.select_related("source_site").filter(pk=options["template_id"]).first()
        if template is None:
            raise CommandError(f"WebsiteTemplate id={options['template_id']} was not found.")

        source_site = template.source_site
        requested_source_id = options.get("source_site_id")
        if requested_source_id is not None:
            source_site = Site.objects.filter(pk=requested_source_id).first()
            if source_site is None:
                raise CommandError(f"Site id={requested_source_id} was not found.")

        snapshot = normalize_template_snapshot(template, build_site_snapshot(source_site))
        validate_template_snapshot(snapshot)

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"snapshot valid template={template.pk} source_site={source_site.pk} "
                    f"sections={len(snapshot['sections'])} pages={len(snapshot['pages'])}"
                )
            )
            return

        with transaction.atomic():
            locked_template = WebsiteTemplate.objects.select_for_update().get(pk=template.pk)
            locked_template.source_site = source_site
            locked_template.snapshot_config = snapshot
            locked_template.save(update_fields=["source_site", "snapshot_config", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"snapshot updated template={template.pk} source_site={source_site.pk} "
                f"sections={len(snapshot['sections'])} pages={len(snapshot['pages'])}"
            )
        )
