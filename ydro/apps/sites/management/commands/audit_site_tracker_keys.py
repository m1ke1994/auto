from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from apps.analytics.models import TrackingEvent
from apps.sites.models import Site
from apps.sites.services import is_technical_template_source_site, site_metadata
from apps.sites.tracker_utils import mask_tracker_token
from tracker.models import Event as TrackerEvent
from tracker.models import Site as TrackerSite


class Command(BaseCommand):
    help = "Read-only audit of public site tracker keys and recent analytics isolation."

    def handle(self, *args, **options):
        since = timezone.now() - timezone.timedelta(hours=24)
        duplicate_keys = set(
            Site.objects.values("api_key")
            .annotate(key_count=Count("id"))
            .filter(key_count__gt=1)
            .values_list("api_key", flat=True)
        )

        headers = [
            "site_id",
            "name",
            "slug",
            "domain",
            "owner_id",
            "masked_api_key",
            "duplicate_api_key",
            "status",
            "render_mode",
            "technical_source",
            "event_count_24h",
            "rejected_events_24h",
        ]
        self.stdout.write("\t".join(headers))

        tracker_sites_by_token = {
            tracker_site.token: tracker_site
            for tracker_site in TrackerSite.objects.filter(token__in=Site.objects.values("api_key"))
        }

        for site in Site.objects.select_related("owner").order_by("id"):
            metadata = site_metadata(site)
            tracker_site = tracker_sites_by_token.get(site.api_key)
            tracker_events = (
                TrackerEvent.objects.filter(visit__site=tracker_site, timestamp__gte=since).count()
                if tracker_site is not None
                else 0
            )
            core_events = TrackingEvent.objects.filter(visit__site=site, timestamp__gte=since).count()
            status_value = metadata.get("status") or ("active" if site.is_active else "inactive")
            row = [
                str(site.id),
                site.name,
                site.slug,
                site.domain or "",
                str(site.owner_id),
                mask_tracker_token(site.api_key),
                "yes" if site.api_key in duplicate_keys else "no",
                status_value,
                metadata.get("render_mode") or "",
                "yes" if is_technical_template_source_site(site) else "no",
                str(tracker_events + core_events),
                "n/a",
            ]
            self.stdout.write("\t".join(str(value).replace("\t", " ").replace("\n", " ") for value in row))
