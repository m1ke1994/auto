from collections import Counter
from urllib.parse import urlparse

from django.db.models import Avg, Count

from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.sites.models import SiteLead
from seo_audit.models import SiteSEOAudit

PERSONAL_KEYS = frozenset({"name", "email", "phone", "ip", "ip_address", "cookie", "session_id", "visitor_id", "password", "token", "message"})


def _assert_anonymous(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PERSONAL_KEYS:
                raise ValueError(f"personal field in AI payload: {key}")
            _assert_anonymous(child)
    elif isinstance(value, list):
        for child in value: _assert_anonymous(child)


def build_payload(*, job):
    site, date_from, date_to = job.site, job.period_from, job.period_to
    visits = Visit.objects.filter(site=site, started_at__date__gte=date_from, started_at__date__lte=date_to, is_bot=False)
    pageviews = PageView.objects.filter(visit__site=site, timestamp__date__gte=date_from, timestamp__date__lte=date_to, visit__is_bot=False)
    events = TrackingEvent.objects.filter(visit__site=site, timestamp__date__gte=date_from, timestamp__date__lte=date_to, visit__is_bot=False)
    visit_count, page_count = visits.count(), pageviews.count()
    unique = visits.exclude(visitor_id="").values("visitor_id").distinct().count()
    leads = SiteLead.objects.filter(site=site, created_at__date__gte=date_from, created_at__date__lte=date_to).count()
    devices = {"unknown": visit_count}
    sources = Counter((urlparse(value).hostname or "direct") if value else "direct" for value in visits.values_list("referrer", flat=True))
    top_pages = [{"path": row["pathname"] or "/", "views": row["count"]} for row in pageviews.values("pathname").annotate(count=Count("id")).order_by("-count")[:20]]
    event_counts = {row["type"]: row["count"] for row in events.values("type").annotate(count=Count("id"))}
    audit = SiteSEOAudit.objects.filter(domain__iexact=site.domain).order_by("-created_at").first()
    payload = {
        "external_job_id": str(job.external_job_id), "site_id": site.id, "site_domain": site.domain,
        "recommendation_type": job.recommendation_type, "language": "ru",
        "period": {"date_from": str(date_from), "date_to": str(date_to)},
        "site_context": {"site_name": site.name, "business_type": "", "description": ""},
        "analytics": {
            "visits": visit_count, "unique_visitors": unique, "page_views": page_count,
            "average_session_duration_seconds": round(visits.aggregate(value=Avg("duration"))["value"] or 0),
            "bounce_rate": round(visits.filter(pageviews__isnull=True).count() / visit_count, 4) if visit_count else 0,
            "conversion_rate": round(leads / visit_count, 4) if visit_count else 0, "leads": leads,
            "traffic_sources": [{"source": source[:100], "visits": count} for source, count in sources.most_common(20)],
            "top_pages": top_pages, "events": event_counts, "devices": devices, "browsers": {}, "countries": {},
            "performance": {}, "errors": [],
        },
        "seo": {"score": getattr(audit, "seo_score", None), "issues": [], "pages": [], "keywords": []},
        "options": {"max_recommendations": 10, "include_summary": True},
    }
    _assert_anonymous(payload)
    return payload
