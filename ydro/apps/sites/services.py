from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable
from urllib.parse import urlparse

from django.db import connection, transaction
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

logger = logging.getLogger(__name__)


class SiteOperationConflict(Exception):
    pass


class ProtectedSiteError(Exception):
    pass


class ProtectedTemplateSourceError(ProtectedSiteError):
    pass


class WebsiteTemplateNotFoundError(Exception):
    pass


class WebsiteTemplateInUseError(Exception):
    def __init__(self, cloned_sites_count: int):
        self.cloned_sites_count = cloned_sites_count
        super().__init__("Шаблон используется клиентскими сайтами и не может быть удалён.")


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

TEMPLATE_TABLE = "sites_websitetemplate"
TEMPLATE_SOURCE_SITE_COLUMNS = ("source_site_id",)
TEMPLATE_SOURCE_SITE_FALLBACK_COLUMNS = ("source_site_id", "site_id")
TEMPLATE_SOURCE_SLUG_PREFIX = "tracknode-template-"
TEMPLATE_NAME_FALLBACK_COLUMNS = ("name", "title", "slug")
TEMPLATE_CLONE_REQUEST_FALLBACK_TEMPLATE_COLUMNS = (
    "template_id",
    "website_template_id",
)
TEMPLATE_CLONE_REQUEST_TABLE = "sites_websitetemplateclonerequest"
TEMPLATE_CLONE_REQUEST_FALLBACK_SITE_COLUMNS = (
    "site_id",
    "created_site_id",
    "cloned_site_id",
)


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


def _table_exists(table_name: str) -> bool:
    with connection.cursor() as cursor:
        return table_name in connection.introspection.table_names(cursor)


def _table_columns(table_name: str) -> set[str]:
    with connection.cursor() as cursor:
        return {column.name for column in connection.introspection.get_table_description(cursor, table_name)}


def _site_fk_columns(
    table_name: str,
    *,
    fallback_columns: tuple[str, ...] = TEMPLATE_CLONE_REQUEST_FALLBACK_SITE_COLUMNS,
) -> list[str]:
    if not _table_exists(table_name):
        return []

    columns = _table_columns(table_name)
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kcu.column_name
                  FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                   AND tc.table_schema = kcu.table_schema
                  JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                   AND ccu.table_schema = tc.table_schema
                 WHERE tc.constraint_type = 'FOREIGN KEY'
                   AND tc.table_name = %s
                   AND ccu.table_name = 'sites_site'
                   AND ccu.column_name = 'id'
                 ORDER BY kcu.ordinal_position
                """,
                [table_name],
            )
            fk_columns = [row[0] for row in cursor.fetchall() if row[0] in columns]
            if fk_columns:
                return fk_columns

    return [column for column in fallback_columns if column in columns]


def _template_fk_columns(table_name: str) -> list[str]:
    if not _table_exists(table_name):
        return []

    columns = _table_columns(table_name)
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kcu.column_name
                  FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                   AND tc.table_schema = kcu.table_schema
                  JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                   AND ccu.table_schema = tc.table_schema
                 WHERE tc.constraint_type = 'FOREIGN KEY'
                   AND tc.table_name = %s
                   AND ccu.table_name = %s
                   AND ccu.column_name = 'id'
                 ORDER BY kcu.ordinal_position
                """,
                [table_name, TEMPLATE_TABLE],
            )
            fk_columns = [row[0] for row in cursor.fetchall() if row[0] in columns]
            if fk_columns:
                return fk_columns

    return [column for column in TEMPLATE_CLONE_REQUEST_FALLBACK_TEMPLATE_COLUMNS if column in columns]


def _template_source_site_columns() -> list[str]:
    columns = _site_fk_columns(TEMPLATE_TABLE, fallback_columns=TEMPLATE_SOURCE_SITE_FALLBACK_COLUMNS)
    preferred = [column for column in TEMPLATE_SOURCE_SITE_COLUMNS if column in columns]
    return preferred or columns


def template_source_site_ids() -> set[int]:
    columns = _template_source_site_columns()
    if not columns:
        return set()

    table = connection.ops.quote_name(TEMPLATE_TABLE)
    ids: set[int] = set()
    with connection.cursor() as cursor:
        for column in columns:
            quoted_column = connection.ops.quote_name(column)
            cursor.execute(f"SELECT DISTINCT {quoted_column} FROM {table} WHERE {quoted_column} IS NOT NULL")
            ids.update(int(row[0]) for row in cursor.fetchall() if row[0] is not None)
    return ids


def is_template_source_site(site: Site | int | None) -> bool:
    if site is None:
        return False

    site_id = int(site if isinstance(site, int) else site.id)
    if site_id in template_source_site_ids():
        return True

    slug = "" if isinstance(site, int) else str(getattr(site, "slug", "") or "")
    return slug.startswith(TEMPLATE_SOURCE_SLUG_PREFIX)


def filter_client_manageable_sites(queryset: QuerySet[Site]) -> QuerySet[Site]:
    source_ids = template_source_site_ids()
    if source_ids:
        queryset = queryset.exclude(id__in=source_ids)
    return queryset.exclude(slug__startswith=TEMPLATE_SOURCE_SLUG_PREFIX)


def _delete_template_clone_requests(snapshot: SiteSnapshot) -> int:
    columns = _site_fk_columns(TEMPLATE_CLONE_REQUEST_TABLE)
    if not columns:
        return 0

    where = " OR ".join(f"{connection.ops.quote_name(column)} = %s" for column in columns)
    params = [snapshot.id] * len(columns)
    table = connection.ops.quote_name(TEMPLATE_CLONE_REQUEST_TABLE)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params)
        count = int(cursor.fetchone()[0] or 0)
        if count:
            cursor.execute(f"DELETE FROM {table} WHERE {where}", params)
    return count


def _template_clone_request_count(snapshot: SiteSnapshot) -> int:
    columns = _site_fk_columns(TEMPLATE_CLONE_REQUEST_TABLE)
    if not columns:
        return 0

    table = connection.ops.quote_name(TEMPLATE_CLONE_REQUEST_TABLE)
    where = " OR ".join(f"{connection.ops.quote_name(column)} = %s" for column in columns)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", [snapshot.id] * len(columns))
        return int(cursor.fetchone()[0] or 0)


def _template_clone_request_where_for_template(template_id: int) -> tuple[str, list[int]]:
    columns = _template_fk_columns(TEMPLATE_CLONE_REQUEST_TABLE)
    if not columns:
        return "", []
    where = " OR ".join(f"{connection.ops.quote_name(column)} = %s" for column in columns)
    return where, [template_id] * len(columns)


def _template_clone_sites_count(template_id: int, *, source_site_id: int | None = None) -> int:
    if not _table_exists(TEMPLATE_CLONE_REQUEST_TABLE):
        return 0

    where, params = _template_clone_request_where_for_template(template_id)
    if not where:
        return 0

    site_columns = _site_fk_columns(TEMPLATE_CLONE_REQUEST_TABLE)
    table = connection.ops.quote_name(TEMPLATE_CLONE_REQUEST_TABLE)
    cloned_site_ids: set[int] = set()
    with connection.cursor() as cursor:
        for column in site_columns:
            quoted_column = connection.ops.quote_name(column)
            cursor.execute(f"SELECT {quoted_column} FROM {table} WHERE ({where}) AND {quoted_column} IS NOT NULL", params)
            cloned_site_ids.update(int(row[0]) for row in cursor.fetchall() if row[0] is not None)

        if cloned_site_ids:
            cloned_site_ids.discard(source_site_id)
            return len(cloned_site_ids)

        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params)
        return int(cursor.fetchone()[0] or 0)


def _delete_template_clone_requests_for_template(template_id: int) -> int:
    if not _table_exists(TEMPLATE_CLONE_REQUEST_TABLE):
        return 0

    where, params = _template_clone_request_where_for_template(template_id)
    if not where:
        return 0

    table = connection.ops.quote_name(TEMPLATE_CLONE_REQUEST_TABLE)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params)
        count = int(cursor.fetchone()[0] or 0)
        if count:
            cursor.execute(f"DELETE FROM {table} WHERE {where}", params)
    return count


def _template_row(template_id: int) -> dict | None:
    if not _table_exists(TEMPLATE_TABLE):
        return None

    columns = _table_columns(TEMPLATE_TABLE)
    source_columns = _template_source_site_columns()
    if not source_columns:
        return None

    table = connection.ops.quote_name(TEMPLATE_TABLE)
    if len(source_columns) == 1:
        source_expression = connection.ops.quote_name(source_columns[0])
    else:
        source_expression = "COALESCE(%s)" % ", ".join(connection.ops.quote_name(column) for column in source_columns)
    name_column = next((column for column in TEMPLATE_NAME_FALLBACK_COLUMNS if column in columns), None)
    name_expression = connection.ops.quote_name(name_column) if name_column else "''"

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id, {source_expression}, {name_expression} FROM {table} WHERE id = %s",
            [template_id],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {"id": int(row[0]), "source_site_id": row[1], "name": str(row[2] or "")}


def website_template_for_source_site(site_id: int) -> dict | None:
    if not _table_exists(TEMPLATE_TABLE):
        return None

    columns = _table_columns(TEMPLATE_TABLE)
    source_columns = _template_source_site_columns()
    if not source_columns:
        return None

    table = connection.ops.quote_name(TEMPLATE_TABLE)
    name_column = next((column for column in TEMPLATE_NAME_FALLBACK_COLUMNS if column in columns), None)
    name_expression = connection.ops.quote_name(name_column) if name_column else "''"
    where = " OR ".join(f"{connection.ops.quote_name(column)} = %s" for column in source_columns)
    params = [site_id] * len(source_columns)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, {name_expression} FROM {table} WHERE {where} LIMIT 1", params)
        row = cursor.fetchone()
    if row is None:
        return None

    template_id = int(row[0])
    name = str(row[1] or "")
    return {
        "id": template_id,
        "name": name,
        "source_site_id": site_id,
        "cloned_sites_count": _template_clone_sites_count(template_id, source_site_id=site_id),
    }


def _delete_template_row(template_id: int) -> int:
    table = connection.ops.quote_name(TEMPLATE_TABLE)
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", [template_id])
        return int(cursor.rowcount or 0)


def _has_running_site_jobs(site: Site) -> bool:
    client = _client_for_site(site)
    return (
        CompetitorAnalysis.objects.filter(site=site, status__in=RUNNING_COMPETITOR_STATUSES).exists()
        or AIRecommendationJob.objects.filter(site=site, status__in=RUNNING_AI_STATUSES, deleted_at__isnull=True).exists()
        or _seo_audits(site, client).filter(status__in=RUNNING_SEO_STATUSES).exists()
    )


def _ensure_deletable_site(site: Site, *, allow_template_source: bool = False) -> None:
    if site.slug == TRACKNODE_SITE_SLUG:
        raise ProtectedSiteError("Системный сайт TrackNode нельзя удалить.")


    if not allow_template_source and is_template_source_site(site):
        raise ProtectedTemplateSourceError("Источник шаблона нельзя удалить из раздела «Мои сайты».")


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


def _log_deletion_stage(stage: str, *, snapshot: SiteSnapshot | None = None, user_id: int | None = None, extra: dict | None = None) -> None:
    payload = {
        "stage": stage,
        "user_id": user_id,
        "site_id": snapshot.id if snapshot else None,
        "site_slug": snapshot.slug if snapshot else "",
    }
    if extra:
        payload.update(extra)
    logger.info("site.delete stage=%s payload=%s", stage, payload)


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
    counts["template_clone_requests"] = _template_clone_request_count(SiteSnapshot.from_site(site))
    return counts


def _legacy_leads(site: Site, client: Client | None = None):
    from leads.models import Lead

    client = client or _client_for_site(site)
    if client is None:
        return Lead.objects.none()
    return Lead.objects.filter(client=client).filter(_url_matches_domain_q("source_url", site.domain or site.slug))


def delete_owned_site(*, site: Site, request, allow_template_source: bool = False) -> dict:
    user_id = getattr(getattr(request, "user", None), "id", None)
    _ensure_deletable_site(site, allow_template_source=allow_template_source)
    if _has_running_site_jobs(site):
        raise SiteOperationConflict("Для сайта уже выполняется фоновая задача. Повторите позже.")

    with transaction.atomic():
        _log_deletion_stage("resolve_site", user_id=user_id, extra={"site_id": site.pk})
        locked_site = Site.objects.select_for_update().select_related("owner").get(pk=site.pk, owner=site.owner)
        _ensure_deletable_site(locked_site, allow_template_source=allow_template_source)
        snapshot = SiteSnapshot.from_site(locked_site)
        _log_deletion_stage("collect_counts", snapshot=snapshot, user_id=user_id)
        deleted = _site_delete_counts(locked_site)
        client = _client_for_site(locked_site)
        tracker_site = _tracker_site(locked_site)
        media_files = list(MediaFile.objects.filter(site=locked_site).exclude(file="").values_list("file", flat=True))

        _log_deletion_stage("delete_legacy_analytics", snapshot=snapshot, user_id=user_id)
        _delete_queryset(_legacy_clicks(locked_site, client))
        _delete_queryset(_legacy_events(locked_site, client))
        _delete_queryset(_legacy_pageviews(locked_site, client))
        _delete_queryset(_legacy_leads(locked_site, client))
        _log_deletion_stage("delete_seo", snapshot=snapshot, user_id=user_id)
        _delete_queryset(_seo_audits(locked_site, client))
        _log_deletion_stage("delete_tracker", snapshot=snapshot, user_id=user_id)
        if tracker_site is not None:
            tracker_site.delete()
        _log_deletion_stage("delete_template_clone_requests", snapshot=snapshot, user_id=user_id)
        deleted["template_clone_requests"] = _delete_template_clone_requests(snapshot)
        _log_deletion_stage("delete_site", snapshot=snapshot, user_id=user_id)
        locked_site.delete()

        _log_deletion_stage("write_audit", snapshot=snapshot, user_id=user_id)
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
                if not file_name:
                    continue
                try:
                    if not MediaFile.objects.filter(file=file_name).exists():
                        MediaFile._meta.get_field("file").storage.delete(file_name)
                except Exception:
                    logger.exception(
                        "site.delete file cleanup failed stage=schedule_file_cleanup site_id=%s file=%s",
                        snapshot.id,
                        file_name,
                    )

        _log_deletion_stage("schedule_file_cleanup", snapshot=snapshot, user_id=user_id, extra={"files": len(media_files)})
        transaction.on_commit(delete_unreferenced_files)

    _log_deletion_stage("build_response", snapshot=snapshot, user_id=user_id)
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


def delete_website_template(*, template_id: int, confirmation: str, request) -> dict:
    template = _template_row(template_id)
    if template is None:
        raise WebsiteTemplateNotFoundError("Шаблон не найден.")

    source_site_id = template["source_site_id"]
    template_name = template["name"] or str(template_id)
    cloned_sites_count = _template_clone_sites_count(template_id, source_site_id=source_site_id)
    if cloned_sites_count:
        raise WebsiteTemplateInUseError(cloned_sites_count)
    if str(confirmation or "").strip() != template_name:
        raise ValueError("Введите точное название шаблона для подтверждения удаления.")

    with transaction.atomic():
        template = _template_row(template_id)
        if template is None:
            raise WebsiteTemplateNotFoundError("Шаблон не найден.")

        source_site_id = template["source_site_id"]
        template_name = template["name"] or str(template_id)
        cloned_sites_count = _template_clone_sites_count(template_id, source_site_id=source_site_id)
        if cloned_sites_count:
            raise WebsiteTemplateInUseError(cloned_sites_count)

        source_site = Site.objects.select_for_update().filter(pk=source_site_id).select_related("owner").first()
        deleted_clone_requests = _delete_template_clone_requests_for_template(template_id)
        deleted_templates = _delete_template_row(template_id)
        source_delete_result = None
        if source_site is not None:
            source_delete_result = delete_owned_site(
                site=source_site,
                request=request,
                allow_template_source=True,
            )

        PlatformAuditLog.objects.create(
            actor=request.user,
            action="template.delete",
            site=None,
            client_id=None,
            object_type="sites.WebsiteTemplate",
            object_id=str(template_id),
            ip_address=_client_ip(request),
            metadata={
                "result": "success",
                "template": {
                    "id": template_id,
                    "name": template_name,
                    "source_site_id": source_site_id,
                },
                "deleted": {
                    "templates": deleted_templates,
                    "template_clone_requests": deleted_clone_requests,
                    "source_site": 1 if source_delete_result else 0,
                },
            },
        )

    return {
        "success": True,
        "template_id": str(template_id),
        "template_name": template_name,
        "source_site_id": source_site_id,
        "deleted": {
            "templates": deleted_templates,
            "template_clone_requests": deleted_clone_requests,
            "source_site": 1 if source_delete_result else 0,
        },
        "source_site": (source_delete_result or {}).get("site"),
    }
