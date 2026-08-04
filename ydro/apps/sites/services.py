from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from django.db import transaction
from django.db.models import Q, QuerySet

from ai_recommendations.models import AIRecommendationJob
from analytics_app.models import ClickEvent as LegacyClickEvent
from analytics_app.models import Event as LegacyEvent
from analytics_app.models import PageView as LegacyPageView
from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.mediafiles.models import MediaFile
from apps.sites.tracknode_site import TRACKNODE_SITE_SLUG
from clients.models import Client
from competitor_analysis.models import CompetitorAnalysis
from platform_admin.models import PlatformAuditLog
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from tracker.models import Event as TrackerEvent
from tracker.models import PageView as TrackerPageView
from tracker.models import Site as TrackerSite
from tracker.models import Visit as TrackerVisit

from .models import Site, SiteLead, SiteSection


class SiteOperationConflict(Exception):
    pass


class ProtectedSiteError(Exception):
    pass


RUNNING_COMPETITOR_STATUSES = {
    CompetitorAnalysis.Status.PENDING,
    CompetitorAnalysis.Status.RUNNING,
}
RUNNING_AI_STATUSES = {
    AIRecommendationJob.Status.QUEUED,
    AIRecommendationJob.Status.PROCESSING,
}
RUNNING_SEO_STATUSES = {
    SiteSEOAudit.Status.PENDING,
    SiteSEOAudit.Status.RUNNING,
}


@dataclass(frozen=True)
class SiteSnapshot:
    id: int
    name: str
    slug: str
    domain: str
    api_key: str
    owner_id: int
    client_id: int | None

    @classmethod
    def from_site(cls, site: Site) -> "SiteSnapshot":
        client = getattr(getattr(site, "owner", None), "client", None)
        return cls(
            id=site.id,
            name=site.name,
            slug=site.slug,
            domain=site.domain or "",
            api_key=site.api_key,
            owner_id=site.owner_id,
            client_id=getattr(client, "id", None),
        )


def _client_for_site(site: Site) -> Client | None:
    return Client.objects.filter(owner=site.owner).first()


def _normalize_domain(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return (parsed.netloc or parsed.path).strip().strip("/")


def _url_matches_domain_q(field_name: str, domain: str) -> Q:
    domain = _normalize_domain(domain)
    if not domain:
        return Q(pk__in=[])
    return (
        Q(**{f"{field_name}__iexact": f"http://{domain}"})
        | Q(**{f"{field_name}__iexact": f"https://{domain}"})
        | Q(**{f"{field_name}__istartswith": f"http://{domain}/"})
        | Q(**{f"{field_name}__istartswith": f"https://{domain}/"})
        | Q(**{f"{field_name}__istartswith": f"http://{domain}?"})
        | Q(**{f"{field_name}__istartswith": f"https://{domain}?"})
    )


def _site_domain_q(site: Site) -> Q:
    domains = {_normalize_domain(site.domain), _normalize_domain(site.slug)}
    query = Q(pk__in=[])
    for domain in domains:
        if domain:
            query |= Q(domain__iexact=domain)
    return query


def _legacy_pageviews(site: Site, client: Client | None = None) -> QuerySet[LegacyPageView]:
    client = client or _client_for_site(site)
    if client is None:
        return LegacyPageView.objects.none()
    return LegacyPageView.objects.filter(client=client).filter(_url_matches_domain_q("url", site.domain or site.slug))


def _legacy_events(site: Site, client: Client | None = None) -> QuerySet[LegacyEvent]:
    client = client or _client_for_site(site)
    if client is None:
        return LegacyEvent.objects.none()
    return LegacyEvent.objects.filter(client=client).filter(_url_matches_domain_q("page_url", site.domain or site.slug))


def _legacy_clicks(site: Site, client: Client | None = None) -> QuerySet[LegacyClickEvent]:
    client = client or _client_for_site(site)
    if client is None:
        return LegacyClickEvent.objects.none()
    session_ids = _legacy_pageviews(site, client).values("session_id").distinct()
    return LegacyClickEvent.objects.filter(client=client, session_id__in=session_ids)


def _seo_audits(site: Site, client: Client | None = None) -> QuerySet[SiteSEOAudit]:
    client = client or _client_for_site(site)
    if client is None:
        return SiteSEOAudit.objects.none()
    return SiteSEOAudit.objects.filter(client=client).filter(_site_domain_q(site))


def _tracker_site(site: Site) -> TrackerSite | None:
    return TrackerSite.objects.filter(token=site.api_key).first()


def _count(querysets: Iterable[tuple[str, QuerySet]]) -> dict[str, int]:
    return {name: queryset.count() for name, queryset in querysets}


def _delete_queryset(queryset: QuerySet) -> int:
    deleted, _details = queryset.delete()
    return int(deleted or 0)


def _has_running_site_jobs(site: Site) -> bool:
    client = _client_for_site(site)
    return (
        CompetitorAnalysis.objects.filter(site=site, status__in=RUNNING_COMPETITOR_STATUSES).exists()
        or AIRecommendationJob.objects.filter(site=site, status__in=RUNNING_AI_STATUSES, deleted_at__isnull=True).exists()
        or _seo_audits(site, client).filter(status__in=RUNNING_SEO_STATUSES).exists()
    )


def _ensure_deletable_site(site: Site) -> None:
    if site.slug == TRACKNODE_SITE_SLUG:
        raise ProtectedSiteError("Системный сайт TrackNode нельзя удалить.")


def _audit_metadata(request, *, result: str, deleted: dict[str, int], error: str = "", snapshot: SiteSnapshot) -> dict:
    meta = getattr(request, "META", {})
    return {
        "result": result,
        "deleted": deleted,
        "deleted_total": sum(deleted.values()),
        "error": error,
        "site": {
            "id": snapshot.id,
            "name": snapshot.name,
            "slug": snapshot.slug,
            "domain": snapshot.domain,
            "owner_id": snapshot.owner_id,
        },
        "user_agent": str(meta.get("HTTP_USER_AGENT", ""))[:1000],
    }


def _client_ip(request) -> str | None:
    meta = getattr(request, "META", {})
    forwarded = str(meta.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or meta.get("REMOTE_ADDR") or None


def log_site_operation(request, *, site: Site | None, snapshot: SiteSnapshot, action: str, result: str, deleted: dict[str, int] | None = None, error: str = "") -> None:
    PlatformAuditLog.objects.create(
        actor=request.user,
        action=action,
        site=site,
        client_id=snapshot.client_id,
        object_type="sites.Site",
        object_id=str(snapshot.id),
        ip_address=_client_ip(request),
        metadata=_audit_metadata(
            request,
            result=result,
            deleted=deleted or {},
            error=error,
            snapshot=snapshot,
        ),
    )


def _analytics_counts(site: Site) -> dict[str, int]:
    client = _client_for_site(site)
    tracker_site = _tracker_site(site)
    tracker_events = TrackerEvent.objects.none()
    tracker_pageviews = TrackerPageView.objects.none()
    tracker_visits = TrackerVisit.objects.none()
    if tracker_site is not None:
        tracker_events = TrackerEvent.objects.filter(visit__site=tracker_site)
        tracker_pageviews = TrackerPageView.objects.filter(visit__site=tracker_site)
        tracker_visits = TrackerVisit.objects.filter(site=tracker_site)

    seo_audits = _seo_audits(site, client)
    return _count(
        (
            ("analytics_events", TrackingEvent.objects.filter(visit__site=site)),
            ("analytics_pageviews", PageView.objects.filter(visit__site=site)),
            ("analytics_visits", Visit.objects.filter(site=site)),
            ("tracker_events", tracker_events),
            ("tracker_pageviews", tracker_pageviews),
            ("tracker_visits", tracker_visits),
            ("legacy_events", _legacy_events(site, client)),
            ("legacy_pageviews", _legacy_pageviews(site, client)),
            ("legacy_clicks", _legacy_clicks(site, client)),
            ("seo_issues", SEOIssue.objects.filter(page__audit__in=seo_audits)),
            ("seo_pages", SEOPage.objects.filter(audit__in=seo_audits)),
            ("seo_audits", seo_audits),
            ("competitor_analyses", CompetitorAnalysis.objects.filter(site=site)),
            ("ai_recommendation_jobs", AIRecommendationJob.objects.filter(site=site)),
        )
    )


def clear_site_analytics(*, site: Site, request) -> dict:
    snapshot = SiteSnapshot.from_site(site)
    if _has_running_site_jobs(site):
        raise SiteOperationConflict("Для сайта уже выполняется аналитическая задача. Повторите позже.")

    with transaction.atomic():
        locked_site = Site.objects.select_for_update().select_related("owner").get(pk=site.pk, owner=site.owner)
        snapshot = SiteSnapshot.from_site(locked_site)
        deleted = _analytics_counts(locked_site)
        client = _client_for_site(locked_site)
        tracker_site = _tracker_site(locked_site)
        seo_audits = _seo_audits(locked_site, client)

        _delete_queryset(_legacy_clicks(locked_site, client))
        _delete_queryset(_legacy_events(locked_site, client))
        _delete_queryset(_legacy_pageviews(locked_site, client))
        _delete_queryset(seo_audits)
        _delete_queryset(CompetitorAnalysis.objects.filter(site=locked_site))
        _delete_queryset(AIRecommendationJob.objects.filter(site=locked_site))
        if tracker_site is not None:
            _delete_queryset(TrackerVisit.objects.filter(site=tracker_site))
        _delete_queryset(Visit.objects.filter(site=locked_site))

        log_site_operation(
            request,
            site=locked_site,
            snapshot=snapshot,
            action="site.analytics.clear",
            result="success",
            deleted=deleted,
        )

    return {
        "success": True,
        "site_id": str(snapshot.id),
        "deleted_total": sum(deleted.values()),
        "deleted": deleted,
    }


def _site_delete_counts(site: Site) -> dict[str, int]:
    client = _client_for_site(site)
    tracker_site = _tracker_site(site)
    counts = _analytics_counts(site)
    counts.update(
        _count(
            (
                ("site_sections", SiteSection.objects.filter(site=site)),
                ("site_leads", SiteLead.objects.filter(site=site)),
                ("media_files", MediaFile.objects.filter(site=site)),
                ("tracker_sites", TrackerSite.objects.filter(pk=tracker_site.pk) if tracker_site else TrackerSite.objects.none()),
                ("legacy_leads", _legacy_leads(site, client)),
            )
        )
    )
    return counts


def _legacy_leads(site: Site, client: Client | None = None):
    from leads.models import Lead

    client = client or _client_for_site(site)
    if client is None:
        return Lead.objects.none()
    return Lead.objects.filter(client=client).filter(_url_matches_domain_q("source_url", site.domain or site.slug))


def delete_owned_site(*, site: Site, request) -> dict:
    _ensure_deletable_site(site)
    if _has_running_site_jobs(site):
        raise SiteOperationConflict("Для сайта уже выполняется фоновая задача. Повторите позже.")

    with transaction.atomic():
        locked_site = Site.objects.select_for_update().select_related("owner").get(pk=site.pk, owner=site.owner)
        _ensure_deletable_site(locked_site)
        snapshot = SiteSnapshot.from_site(locked_site)
        deleted = _site_delete_counts(locked_site)
        client = _client_for_site(locked_site)
        tracker_site = _tracker_site(locked_site)
        media_files = list(MediaFile.objects.filter(site=locked_site).exclude(file="").values_list("file", flat=True))

        _delete_queryset(_legacy_clicks(locked_site, client))
        _delete_queryset(_legacy_events(locked_site, client))
        _delete_queryset(_legacy_pageviews(locked_site, client))
        _delete_queryset(_legacy_leads(locked_site, client))
        _delete_queryset(_seo_audits(locked_site, client))
        if tracker_site is not None:
            tracker_site.delete()
        locked_site.delete()

        log_site_operation(
            request,
            site=None,
            snapshot=snapshot,
            action="site.delete",
            result="success",
            deleted=deleted,
        )

        def delete_unreferenced_files():
            for file_name in media_files:
                if file_name and not MediaFile.objects.filter(file=file_name).exists():
                    MediaFile._meta.get_field("file").storage.delete(file_name)

        transaction.on_commit(delete_unreferenced_files)

    return {
        "success": True,
        "site_id": str(snapshot.id),
        "deleted_total": sum(deleted.values()),
        "deleted": deleted,
        "site": {
            "id": snapshot.id,
            "name": snapshot.name,
            "slug": snapshot.slug,
            "domain": snapshot.domain,
        },
    }
