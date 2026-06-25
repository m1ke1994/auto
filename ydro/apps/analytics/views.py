from collections import Counter, defaultdict
from datetime import datetime, time
from urllib.parse import urlparse

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.models import Site, SiteLead
from apps.sites.tracker_utils import build_tracker_script_tag
from tracker.models import Event as TrackerEvent
from tracker.models import PageView as TrackerPageView
from tracker.models import Site as TrackerSite
from tracker.models import Visit as TrackerVisit
from tracker.services.bot_filter import detect_bot_visit

from .models import PageView, TrackingEvent, Visit
from .serializers import PageViewSerializer, TrackEventSerializer, VisitEndSerializer, VisitStartSerializer


def _client_ip(request):
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or (request.META.get("REMOTE_ADDR") or "")


def _pathname_from_url(value: str) -> str:
    try:
        parsed = urlparse(value or "")
        return parsed.path or "/"
    except Exception:
        return "/"


def _payload_duration_seconds(event) -> int:
    payload = event.payload if isinstance(event.payload, dict) else {}
    for key in ("duration_seconds", "duration", "time_on_page_seconds"):
        try:
            seconds = int(float(payload.get(key) or 0))
        except (TypeError, ValueError):
            seconds = 0
        if seconds > 0:
            return seconds
    for key in ("duration_ms", "duration_milliseconds", "time_on_page_ms"):
        try:
            milliseconds = int(float(payload.get(key) or 0))
        except (TypeError, ValueError):
            milliseconds = 0
        if milliseconds > 0:
            return max(1, round(milliseconds / 1000))
    return 0


def _duration_summary(visits, events) -> tuple[int, int]:
    fallback_by_visit = {}
    for event in events.filter(type="time_on_page"):
        duration_seconds = _payload_duration_seconds(event)
        if duration_seconds <= 0:
            continue
        visit_id = event.visit_id
        fallback_by_visit[visit_id] = max(fallback_by_visit.get(visit_id, 0), duration_seconds)

    total_seconds = 0
    visits_with_duration = 0
    for visit in visits.only("id", "duration"):
        duration_seconds = int(visit.duration or 0)
        if duration_seconds <= 0:
            duration_seconds = fallback_by_visit.get(visit.id, 0)
        if duration_seconds <= 0:
            continue
        total_seconds += duration_seconds
        visits_with_duration += 1

    avg_seconds = round(total_seconds / visits_with_duration) if visits_with_duration else 0
    return total_seconds, avg_seconds


def _unique_visitors_count(visits) -> int:
    visitor_filter = Q(visitor_id__isnull=False) & ~Q(visitor_id="")
    return (
        visits.filter(visitor_filter).values("visitor_id").distinct().count()
        + visits.exclude(visitor_filter).values("session_id").distinct().count()
    )


def _distribution_dict(visits, field_name: str, *, allowed=None, unknown_label="Unknown") -> dict:
    rows = visits.values(field_name).annotate(count=Count("id")).order_by("-count")
    distribution = {}
    for row in rows:
        raw_key = row.get(field_name)
        key = str(raw_key or unknown_label).strip() or unknown_label
        if allowed is not None:
            normalized_key = key.lower()
            if normalized_key not in allowed:
                normalized_key = unknown_label.lower()
            key = normalized_key
        distribution[key] = distribution.get(key, 0) + int(row.get("count") or 0)
    return distribution


def _truthy_query_param(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_period(request, default_days: int = 14):
    tz = timezone.get_current_timezone()
    now = timezone.now()
    raw_from = (request.query_params.get("date_from") or "").strip()
    raw_to = (request.query_params.get("date_to") or "").strip()

    def parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    date_from = parse_date(raw_from)
    date_to = parse_date(raw_to)
    if date_from and date_to:
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        from_dt = timezone.make_aware(datetime.combine(date_from, time.min), tz)
        to_dt = timezone.make_aware(datetime.combine(date_to, time.max), tz)
        return from_dt, to_dt, {"date_from": date_from.isoformat(), "date_to": date_to.isoformat()}

    try:
        days = int(request.query_params.get("days", default_days) or default_days)
    except (TypeError, ValueError):
        days = default_days
    days = min(max(days, 1), 365)
    from_dt = now - timezone.timedelta(days=days)
    return from_dt, now, {"days": days, "date_from": from_dt.date().isoformat(), "date_to": now.date().isoformat()}


def _safe_payload(event) -> dict:
    payload = getattr(event, "payload", {}) or {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _iso(value):
    return value.isoformat() if value else None


def _pageview_path(pageview) -> str:
    pathname = getattr(pageview, "pathname", "") or ""
    return pathname or _pathname_from_url(getattr(pageview, "url", "") or "")


def _event_page_url(event) -> str:
    payload = _safe_payload(event)
    return str(payload.get("page_url") or payload.get("url") or "")


def _event_path(event) -> str:
    payload = _safe_payload(event)
    for key in ("path", "pathname", "page"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value if value.startswith("/") else f"/{value}"
    return _pathname_from_url(_event_page_url(event))


def _event_element(event) -> str:
    payload = _safe_payload(event)
    value = (
        payload.get("element_text")
        or payload.get("text")
        or payload.get("element_id")
        or payload.get("id")
        or payload.get("element_href")
        or payload.get("href")
        or payload.get("element_class")
        or payload.get("class")
        or payload.get("element_tag")
        or payload.get("tag")
        or ""
    )
    return str(value or "").strip()[:120]


def _event_device(event) -> str:
    payload = _safe_payload(event)
    value = payload.get("device_type") or getattr(getattr(event, "visit", None), "device_type", "") or "unknown"
    normalized = str(value or "unknown").strip().lower()
    return normalized if normalized in {"desktop", "mobile", "tablet"} else "unknown"


def _event_browser(event) -> str:
    payload = _safe_payload(event)
    visit = getattr(event, "visit", None)
    return str(payload.get("browser") or getattr(visit, "browser_family", "") or getattr(visit, "browser", "") or "Unknown")


def _event_os(event) -> str:
    payload = _safe_payload(event)
    visit = getattr(event, "visit", None)
    return str(payload.get("os") or getattr(visit, "os", "") or "Unknown")


def _event_visitor_key(event) -> str:
    visit = getattr(event, "visit", None)
    return str(getattr(visit, "visitor_id", "") or getattr(visit, "session_id", "") or "")


def _event_session_id(event) -> str:
    return str(getattr(getattr(event, "visit", None), "session_id", "") or "")


def _sanitize_event_payload(payload: dict) -> dict:
    sanitized = {}
    blocked = {"value", "input", "textarea", "password", "email", "phone", "message"}
    for key, value in (payload or {}).items():
        normalized_key = str(key or "").lower()
        if normalized_key in blocked or normalized_key.endswith("_value"):
            continue
        if normalized_key == "stack":
            sanitized[key] = str(value or "")[:1000]
        elif isinstance(value, str):
            sanitized[key] = value[:1000]
        elif isinstance(value, (int, float, bool)) or value is None:
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = value[:25]
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_event_payload(value)
    return sanitized


def _get_user_site(request, site_id: int):
    queryset = Site.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(owner=request.user)
    return queryset.filter(id=site_id).first()


def _analytics_scope(site: Site, from_dt, to_dt, *, include_bots: bool = False) -> dict:
    tracker_site = TrackerSite.objects.filter(token=site.api_key, is_active=True).first()
    if tracker_site is not None:
        visits = TrackerVisit.objects.filter(site=tracker_site, started_at__gte=from_dt, started_at__lte=to_dt)
        pageviews = TrackerPageView.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt, timestamp__lte=to_dt)
        events = TrackerEvent.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt, timestamp__lte=to_dt)
        if not include_bots:
            visits = visits.filter(is_bot=False)
            pageviews = pageviews.filter(visit__is_bot=False)
            events = events.filter(visit__is_bot=False)
        return {
            "source": "tracker",
            "visits": visits,
            "pageviews": pageviews,
            "events": events,
            "leads": SiteLead.objects.filter(site=site, created_at__gte=from_dt, created_at__lte=to_dt),
        }

    visits = Visit.objects.filter(site=site, started_at__gte=from_dt, started_at__lte=to_dt)
    pageviews = PageView.objects.filter(visit__site=site, timestamp__gte=from_dt, timestamp__lte=to_dt)
    events = TrackingEvent.objects.filter(visit__site=site, timestamp__gte=from_dt, timestamp__lte=to_dt)
    if not include_bots:
        visits = visits.filter(is_bot=False)
        pageviews = pageviews.filter(visit__is_bot=False)
        events = events.filter(visit__is_bot=False)
    return {
        "source": "legacy",
        "visits": visits,
        "pageviews": pageviews,
        "events": events,
        "leads": SiteLead.objects.filter(site=site, created_at__gte=from_dt, created_at__lte=to_dt),
    }


def _filtered_events(events, *, event_type: str = "", page: str = "", device: str = "", limit: int = 5000):
    page = (page or "").strip()
    device = (device or "").strip().lower()
    queryset = events
    if event_type:
        queryset = queryset.filter(type=event_type)
    selected = []
    scan_limit = min(max(limit * 3, limit), 20000)
    for event in queryset.select_related("visit").order_by("-timestamp")[:scan_limit]:
        if page and _event_path(event) != page:
            continue
        if device and device != "all" and _event_device(event) != device:
            continue
        selected.append(event)
        if len(selected) >= limit:
            break
    return selected


def _available_pages(scope: dict, limit: int = 100) -> list[dict]:
    counter = Counter()
    for pageview in scope["pageviews"].select_related("visit").order_by("-timestamp")[:5000]:
        counter[_pageview_path(pageview)] += 1
    for event in scope["events"].select_related("visit").order_by("-timestamp")[:5000]:
        path = _event_path(event)
        if path:
            counter[path] += 0
    return [{"path": path, "count": count} for path, count in counter.most_common(limit)]


class AdminSiteAnalyticsBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def get_site(self, request, site_id: int):
        return _get_user_site(request, site_id)

    def get_context(self, request, site_id: int):
        site = self.get_site(request, site_id)
        if site is None:
            return None, None, None, None
        from_dt, to_dt, period = _parse_period(request)
        include_bots = _truthy_query_param(request.query_params.get("include_bots"))
        return site, _analytics_scope(site, from_dt, to_dt, include_bots=include_bots), period, (from_dt, to_dt)

    def site_not_found(self):
        return Response({"detail": "Site was not found."}, status=status.HTTP_404_NOT_FOUND)


class TrackBaseAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_site(self, token: str) -> Site | None:
        return Site.objects.filter(api_key=token, is_active=True).first()

    def get_or_create_visit(
        self,
        site: Site,
        session_id: str,
        request,
        visitor_id: str = "",
        referrer: str = "",
        tracked_url: str = "",
    ) -> Visit:
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:1000]
        bot_check = detect_bot_visit(
            site_id=site.id,
            ip_address=_client_ip(request),
            user_agent=user_agent,
            tracked_url=tracked_url,
        )
        visit = (
            Visit.objects.filter(site=site, session_id=session_id)
            .order_by("-started_at")
            .first()
        )

        if visit:
            updates = []
            if visitor_id and visit.visitor_id != visitor_id:
                visit.visitor_id = visitor_id
                updates.append("visitor_id")
            if referrer and not visit.referrer:
                visit.referrer = referrer
                updates.append("referrer")
            if bot_check.is_bot and not visit.is_bot:
                visit.is_bot = True
                updates.append("is_bot")
            if bot_check.reason and visit.bot_reason != bot_check.reason:
                visit.bot_reason = bot_check.reason[:255]
                updates.append("bot_reason")
            if updates:
                visit.save(update_fields=updates)
            return visit

        return Visit.objects.create(
            site=site,
            visitor_id=visitor_id or "",
            session_id=session_id,
            ip_address=_client_ip(request),
            is_bot=bot_check.is_bot,
            bot_reason=bot_check.reason[:255],
            user_agent=user_agent,
            referrer=referrer or "",
        )


class VisitStartView(TrackBaseAPIView):
    def post(self, request):
        serializer = VisitStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            referrer=serializer.validated_data.get("referrer") or "",
            tracked_url=request.data.get("url") or "",
        )

        if visit.started_at != serializer.get_started_at():
            visit.started_at = serializer.get_started_at()
            visit.save(update_fields=["started_at"])

        return Response({"ok": True, "visit_id": visit.id}, status=status.HTTP_201_CREATED)


class PageViewCreateView(TrackBaseAPIView):
    def post(self, request):
        serializer = PageViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            tracked_url=serializer.validated_data["url"],
        )

        pageview = PageView.objects.create(
            visit=visit,
            url=serializer.validated_data["url"],
            pathname=_pathname_from_url(serializer.validated_data["url"]),
            title=serializer.validated_data.get("title", ""),
            timestamp=serializer.get_timestamp(),
        )
        return Response({"ok": True, "pageview_id": pageview.id}, status=status.HTTP_201_CREATED)


class EventCreateView(TrackBaseAPIView):
    def post(self, request):
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        event_payload = serializer.validated_data.get("payload") or {}
        tracked_url = event_payload.get("url") if isinstance(event_payload, dict) else ""
        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            tracked_url=tracked_url or "",
        )

        event = TrackingEvent.objects.create(
            visit=visit,
            type=serializer.validated_data["type"],
            payload=event_payload if isinstance(event_payload, dict) else {},
            timestamp=serializer.get_timestamp(),
        )
        return Response({"ok": True, "event_id": event.id}, status=status.HTTP_201_CREATED)


class VisitEndView(TrackBaseAPIView):
    def post(self, request):
        serializer = VisitEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = (
            Visit.objects.filter(site=site, session_id=serializer.validated_data["session_id"])
            .order_by("-started_at")
            .first()
        )
        if visit is None:
            visit = self.get_or_create_visit(
                site=site,
                session_id=serializer.validated_data["session_id"],
                request=request,
                visitor_id=serializer.validated_data.get("visitor_id") or "",
            )

        ended_at = serializer.get_ended_at()
        duration = serializer.validated_data.get("duration")
        if duration is None:
            duration = max(0, int((ended_at - visit.started_at).total_seconds()))
        visit.ended_at = ended_at
        visit.duration = duration
        visit.save(update_fields=["ended_at", "duration"])
        return Response({"ok": True, "visit_id": visit.id, "duration": visit.duration}, status=status.HTTP_200_OK)


class AdminSiteAnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_site(self, request, site_id):
        queryset = Site.objects.all()
        if not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)
        return queryset.filter(id=site_id).first()

    def get(self, request, site_id: int):
        site = self._get_site(request, site_id)
        if site is None:
            return Response({"detail": "Site was not found."}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days", 14) or 14)
        days = min(max(days, 1), 365)
        from_dt = timezone.now() - timezone.timedelta(days=days)
        include_bots = _truthy_query_param(request.query_params.get("include_bots"))

        tracker_site = TrackerSite.objects.filter(token=site.api_key, is_active=True).first()
        if tracker_site is not None:
            all_visits = TrackerVisit.objects.filter(site=tracker_site, started_at__gte=from_dt)
            real_visits = all_visits.filter(is_bot=False)
            bot_visits = all_visits.filter(is_bot=True)
            visits = all_visits if include_bots else real_visits
            pageviews = TrackerPageView.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt)
            events = TrackerEvent.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt)
            if not include_bots:
                pageviews = pageviews.filter(visit__is_bot=False)
                events = events.filter(visit__is_bot=False)
            top_pages = list(
                pageviews.values("url")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            for page in top_pages:
                page["pathname"] = _pathname_from_url(page.pop("url", ""))
            sources = list(
                visits.values("referrer")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            devices = _distribution_dict(visits, "device_type", allowed={"desktop", "mobile", "tablet", "unknown"})
            browsers = _distribution_dict(visits, "browser_family")
            os_rows = _distribution_dict(visits, "os")
        else:
            all_visits = Visit.objects.filter(site=site, started_at__gte=from_dt)
            real_visits = all_visits.filter(is_bot=False)
            bot_visits = all_visits.filter(is_bot=True)
            visits = all_visits if include_bots else real_visits
            pageviews = PageView.objects.filter(visit__site=site, timestamp__gte=from_dt)
            events = TrackingEvent.objects.filter(visit__site=site, timestamp__gte=from_dt)
            if not include_bots:
                pageviews = pageviews.filter(visit__is_bot=False)
                events = events.filter(visit__is_bot=False)
            top_pages = list(
                pageviews.values("pathname")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            sources = list(
                visits.values("referrer")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            devices = {}
            browsers = {}
            os_rows = {}
        leads = SiteLead.objects.filter(site=site, created_at__gte=from_dt)

        real_visits_count = real_visits.count()
        bot_visits_count = bot_visits.count()
        total_visits_count = all_visits.count()
        visits_count = visits.count()
        unique_visitors = _unique_visitors_count(visits)
        unique_real_visitors = _unique_visitors_count(real_visits)
        leads_count = leads.count()
        conversion = round((leads_count / real_visits_count) * 100, 2) if real_visits_count else 0

        visits_daily = list(
            visits.annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        leads_daily = list(
            leads.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        total_time_on_site_seconds, avg_duration = _duration_summary(visits, events)

        return Response(
            {
                "period_days": days,
                "include_bots": include_bots,
                "visit_count": visits_count,
                "visitors_unique": unique_visitors,
                "unique_real_visitors": unique_real_visitors,
                "real_visitors": real_visits_count,
                "real_visits": real_visits_count,
                "bot_visitors": bot_visits_count,
                "bot_visits": bot_visits_count,
                "total_visitors": total_visits_count,
                "total_visits": total_visits_count,
                "pageviews_count": pageviews.count(),
                "events_count": events.count(),
                "leads_count": leads_count,
                "conversion": conversion,
                "visits_by_day": visits_daily,
                "leads_by_day": leads_daily,
                "top_pages": top_pages,
                "sources": sources,
                "devices": devices,
                "browsers": browsers,
                "os": os_rows,
                "avg_duration": avg_duration,
                "avg_time_on_site": avg_duration,
                "total_time_on_site_seconds": total_time_on_site_seconds,
                "tracker": {
                    "api_key": site.api_key,
                    "script_tag": build_tracker_script_tag(site.api_key),
                },
            }
        )


class AdminSiteAnalyticsHeatmapView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        page_filter = (request.query_params.get("page") or request.query_params.get("path") or "").strip()
        device_filter = (request.query_params.get("device") or "all").strip().lower()
        click_events = _filtered_events(
            scope["events"],
            event_type="click",
            page=page_filter,
            device=device_filter,
            limit=5000,
        )

        bucket_size = 40
        buckets = {}
        element_counter = Counter()
        page_counter = Counter()
        max_width = 1440
        max_height = 1800

        for event in click_events:
            payload = _safe_payload(event)
            path = _event_path(event)
            page_counter[path] += 1
            element_label = _event_element(event) or "Без подписи"
            element_tag = str(payload.get("element_tag") or payload.get("tag") or "").lower()
            element_counter[(element_label, element_tag, path)] += 1

            scroll_x = _safe_int(payload.get("scroll_x"), 0)
            scroll_y = _safe_int(payload.get("scroll_y"), 0)
            x = _safe_int(payload.get("x"), -1)
            y = _safe_int(payload.get("y"), -1)
            if x < 0:
                client_x = _safe_int(payload.get("client_x"), -1)
                x = client_x + scroll_x if client_x >= 0 else -1
            if y < 0:
                client_y = _safe_int(payload.get("client_y"), -1)
                y = client_y + scroll_y if client_y >= 0 else -1
            if x < 0 or y < 0:
                continue

            max_width = max(max_width, _safe_int(payload.get("document_width"), 0), _safe_int(payload.get("viewport_width"), 0), x + 80)
            max_height = max(max_height, _safe_int(payload.get("document_height"), 0), _safe_int(payload.get("viewport_height"), 0), y + 80)
            bx = round(x / bucket_size) * bucket_size
            by = round(y / bucket_size) * bucket_size
            key = (bx, by)
            current = buckets.setdefault(
                key,
                {
                    "x": bx,
                    "y": by,
                    "count": 0,
                    "page": path,
                    "device": _event_device(event),
                },
            )
            current["count"] += 1

        max_count = max((point["count"] for point in buckets.values()), default=0)
        points = []
        for point in buckets.values():
            intensity = round(point["count"] / max_count, 3) if max_count else 0
            points.append({**point, "intensity": intensity})
        points.sort(key=lambda item: item["count"], reverse=True)

        return Response(
            {
                "period": period,
                "filters": {"page": page_filter, "device": device_filter},
                "total_clicks": len(click_events),
                "canvas": {"width": max_width, "height": max_height, "bucket_size": bucket_size},
                "points": points[:800],
                "top_elements": [
                    {"element": key[0], "tag": key[1], "path": key[2], "count": count}
                    for key, count in element_counter.most_common(30)
                ],
                "pages": _available_pages(scope),
                "page_rows": [{"path": path, "clicks": count} for path, count in page_counter.most_common(50)],
            }
        )


class AdminSiteAnalyticsScrollmapView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        page_filter = (request.query_params.get("page") or request.query_params.get("path") or "").strip()
        events = _filtered_events(scope["events"], event_type="scroll_depth", page=page_filter, limit=10000)
        max_by_session_page = {}
        document_heights = []

        for event in events:
            payload = _safe_payload(event)
            path = _event_path(event)
            session_id = _event_session_id(event)
            if not session_id:
                continue
            depth = max(
                _safe_int(payload.get("max_depth"), 0),
                _safe_int(payload.get("current_depth"), 0),
                _safe_int(payload.get("depth"), 0),
                _safe_int(payload.get("scroll_depth"), 0),
            )
            depth = min(max(depth, 0), 100)
            key = (session_id, path)
            max_by_session_page[key] = max(max_by_session_page.get(key, 0), depth)
            document_height = _safe_int(payload.get("document_height"), 0)
            if document_height > 0:
                document_heights.append(document_height)

        depths = list(max_by_session_page.values())
        average_depth = round(sum(depths) / len(depths), 1) if depths else 0
        thresholds = {}
        for threshold in (25, 50, 75, 100):
            count = sum(1 for depth in depths if depth >= threshold)
            thresholds[str(threshold)] = {
                "count": count,
                "rate": round((count / len(depths)) * 100, 1) if depths else 0,
            }

        page_depths = defaultdict(list)
        for (_session_id, path), depth in max_by_session_page.items():
            page_depths[path].append(depth)
        page_rows = []
        for path, values in page_depths.items():
            page_rows.append(
                {
                    "path": path,
                    "sessions": len(values),
                    "avg_depth": round(sum(values) / len(values), 1) if values else 0,
                }
            )
        page_rows.sort(key=lambda item: (item["avg_depth"], -item["sessions"]))

        return Response(
            {
                "period": period,
                "filters": {"page": page_filter},
                "pages": _available_pages(scope),
                "sessions": len(depths),
                "average_depth": average_depth,
                "thresholds": thresholds,
                "document_height": max(document_heights, default=0),
                "worst_pages": page_rows[:20],
                "page_rows": sorted(page_rows, key=lambda item: item["sessions"], reverse=True)[:50],
            }
        )


class AdminSiteAnalyticsSessionsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        limit = min(max(_safe_int(request.query_params.get("limit"), 50), 1), 100)
        visits = list(scope["visits"].order_by("-started_at")[:limit])
        session_ids = [visit.session_id for visit in visits if getattr(visit, "session_id", "")]
        pageviews_by_session = defaultdict(list)
        events_by_session = defaultdict(list)

        for pageview in (
            scope["pageviews"]
            .filter(visit__session_id__in=session_ids)
            .select_related("visit")
            .order_by("timestamp")[:10000]
        ):
            pageviews_by_session[pageview.visit.session_id].append(pageview)
        for event in (
            scope["events"]
            .filter(visit__session_id__in=session_ids)
            .select_related("visit")
            .order_by("timestamp")[:20000]
        ):
            events_by_session[event.visit.session_id].append(event)

        rows = []
        for visit in visits:
            session_events = events_by_session.get(visit.session_id, [])
            pages = []
            for pageview in pageviews_by_session.get(visit.session_id, []):
                path = _pageview_path(pageview)
                if not pages or pages[-1] != path:
                    pages.append(path)
            click_count = sum(1 for event in session_events if event.type == "click")
            duration = int(getattr(visit, "duration", 0) or 0)
            if duration <= 0:
                duration = max((_payload_duration_seconds(event) for event in session_events), default=0)
            rows.append(
                {
                    "session_id": visit.session_id,
                    "visitor_id": getattr(visit, "visitor_id", "") or "",
                    "started_at": _iso(getattr(visit, "started_at", None)),
                    "ended_at": _iso(getattr(visit, "ended_at", None)),
                    "duration": duration,
                    "device_type": getattr(visit, "device_type", "") or "unknown",
                    "browser": getattr(visit, "browser_family", "") or getattr(visit, "browser", "") or "Unknown",
                    "os": getattr(visit, "os", "") or "Unknown",
                    "clicks": click_count,
                    "events": len(session_events),
                    "pages": pages,
                    "pageviews": len(pageviews_by_session.get(visit.session_id, [])),
                }
            )

        return Response({"period": period, "count": scope["visits"].count(), "results": rows})


class AdminSiteAnalyticsSessionDetailView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int, session_id: str):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        visit = scope["visits"].filter(session_id=session_id).order_by("-started_at").first()
        if visit is None:
            return Response({"detail": "Session was not found."}, status=status.HTTP_404_NOT_FOUND)

        pageviews = [
            {
                "url": pageview.url,
                "path": _pageview_path(pageview),
                "title": getattr(pageview, "title", "") or "",
                "timestamp": _iso(pageview.timestamp),
            }
            for pageview in scope["pageviews"].filter(visit__session_id=session_id).order_by("timestamp")[:500]
        ]
        events = []
        for event in scope["events"].filter(visit__session_id=session_id).order_by("timestamp")[:2000]:
            events.append(
                {
                    "id": event.id,
                    "type": event.type,
                    "timestamp": _iso(event.timestamp),
                    "path": _event_path(event),
                    "element": _event_element(event),
                    "payload": _sanitize_event_payload(_safe_payload(event)),
                }
            )

        return Response(
            {
                "period": period,
                "session": {
                    "session_id": visit.session_id,
                    "visitor_id": getattr(visit, "visitor_id", "") or "",
                    "started_at": _iso(getattr(visit, "started_at", None)),
                    "ended_at": _iso(getattr(visit, "ended_at", None)),
                    "duration": int(getattr(visit, "duration", 0) or 0),
                    "device_type": getattr(visit, "device_type", "") or "unknown",
                    "browser": getattr(visit, "browser_family", "") or getattr(visit, "browser", "") or "Unknown",
                    "os": getattr(visit, "os", "") or "Unknown",
                },
                "pageviews": pageviews,
                "events": events,
            }
        )


class AdminSiteAnalyticsPathsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        pages_by_session = defaultdict(list)
        for pageview in scope["pageviews"].select_related("visit").order_by("visit__session_id", "timestamp")[:20000]:
            session_id = pageview.visit.session_id
            path = _pageview_path(pageview)
            if not pages_by_session[session_id] or pages_by_session[session_id][-1] != path:
                pages_by_session[session_id].append(path)

        converted_sessions = set(
            scope["events"]
            .filter(type__in=["form_submit", "form_submit_success", "lead_submit"])
            .values_list("visit__session_id", flat=True)
            .distinct()
        )
        durations = {
            item["session_id"]: int(item["duration"] or 0)
            for item in scope["visits"].values("session_id", "duration")[:20000]
        }
        rows_by_path = {}
        for session_id, path_list in pages_by_session.items():
            if not path_list:
                continue
            key = tuple(path_list[:8])
            row = rows_by_path.setdefault(
                key,
                {
                    "path": " -> ".join(key),
                    "steps": list(key),
                    "entry_page": key[0],
                    "exit_page": key[-1],
                    "sessions": 0,
                    "converted": 0,
                    "duration_total": 0,
                },
            )
            row["sessions"] += 1
            row["duration_total"] += durations.get(session_id, 0)
            if session_id in converted_sessions:
                row["converted"] += 1

        rows = []
        for row in rows_by_path.values():
            sessions = row["sessions"]
            rows.append(
                {
                    "path": row["path"],
                    "steps": row["steps"],
                    "entry_page": row["entry_page"],
                    "exit_page": row["exit_page"],
                    "sessions": sessions,
                    "conversion": round((row["converted"] / sessions) * 100, 1) if sessions else 0,
                    "avg_duration": round(row["duration_total"] / sessions) if sessions else 0,
                }
            )
        rows.sort(key=lambda item: item["sessions"], reverse=True)
        return Response({"period": period, "paths": rows[:50]})


class AdminSiteAnalyticsFunnelsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        all_sessions = set(scope["visits"].values_list("session_id", flat=True).distinct())
        key_page_sessions = set()
        contact_sessions = set()
        pageviews_by_session = defaultdict(list)
        for pageview in scope["pageviews"].select_related("visit").order_by("timestamp")[:20000]:
            path = _pageview_path(pageview)
            session_id = pageview.visit.session_id
            pageviews_by_session[session_id].append(path)
            normalized = path.lower()
            if normalized not in {"/", ""}:
                key_page_sessions.add(session_id)
            if any(part in normalized for part in ("contact", "kontakty", "contacts", "form", "lead")):
                contact_sessions.add(session_id)

        lead_sessions = set()
        for event in scope["events"].select_related("visit").order_by("-timestamp")[:20000]:
            payload = _safe_payload(event)
            session_id = _event_session_id(event)
            event_type = event.type
            path = _event_path(event).lower()
            href = str(payload.get("href") or payload.get("element_href") or "").lower()
            if event_type in {"form_submit", "form_submit_attempt", "form_visible", "cta_click"}:
                contact_sessions.add(session_id)
            if any(part in href for part in ("tel:", "mailto:", "telegram", "whatsapp")) or any(
                part in path for part in ("contact", "kontakty", "contacts", "form", "lead")
            ):
                contact_sessions.add(session_id)
            if event_type in {"form_submit", "form_submit_success", "lead_submit"}:
                lead_sessions.add(session_id)

        if not key_page_sessions:
            key_page_sessions = set(pageviews_by_session.keys())

        raw_steps = [
            ("visit", "Посетил сайт", all_sessions),
            ("key_page", "Просмотрел ключевую страницу", key_page_sessions),
            ("contact", "Открыл контакты или форму", contact_sessions),
            ("lead", "Отправил заявку", lead_sessions),
        ]
        steps = []
        previous_count = None
        for key, title, sessions in raw_steps:
            count = len(sessions)
            rate = 100 if previous_count is None else (round((count / previous_count) * 100, 1) if previous_count else 0)
            lost = 0 if previous_count is None else max(previous_count - count, 0)
            steps.append({"key": key, "title": title, "users": count, "rate": rate, "lost": lost})
            previous_count = count

        return Response({"period": period, "name": "Базовая воронка", "steps": steps})


class AdminSiteAnalyticsEventsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        event_type = (request.query_params.get("event_type") or "").strip()
        page_filter = (request.query_params.get("page") or "").strip()
        device_filter = (request.query_params.get("device") or "all").strip().lower()
        events = _filtered_events(
            scope["events"],
            event_type=event_type,
            page=page_filter,
            device=device_filter,
            limit=10000,
        )
        rows = {}
        type_counts = Counter()
        for event in events:
            path = _event_path(event)
            element = _event_element(event)
            key = (event.type, path, element)
            row = rows.setdefault(
                key,
                {
                    "event_type": event.type,
                    "page": path,
                    "element": element,
                    "count": 0,
                    "visitors": set(),
                    "last_seen": event.timestamp,
                },
            )
            row["count"] += 1
            row["visitors"].add(_event_visitor_key(event))
            if event.timestamp > row["last_seen"]:
                row["last_seen"] = event.timestamp
            type_counts[event.type] += 1

        result_rows = []
        for row in rows.values():
            result_rows.append(
                {
                    "event_type": row["event_type"],
                    "page": row["page"],
                    "element": row["element"],
                    "count": row["count"],
                    "unique_visitors": len([item for item in row["visitors"] if item]),
                    "last_seen": _iso(row["last_seen"]),
                }
            )
        result_rows.sort(key=lambda item: item["count"], reverse=True)

        return Response(
            {
                "period": period,
                "filters": {"event_type": event_type, "page": page_filter, "device": device_filter},
                "pages": _available_pages(scope),
                "types": [{"type": key, "count": count} for key, count in type_counts.most_common()],
                "events": result_rows[:200],
            }
        )


class AdminSiteAnalyticsPagesView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        views = Counter()
        unique = defaultdict(set)
        pages_by_session = defaultdict(list)
        for pageview in scope["pageviews"].select_related("visit").order_by("timestamp")[:30000]:
            path = _pageview_path(pageview)
            session_id = pageview.visit.session_id
            views[path] += 1
            unique[path].add(getattr(pageview.visit, "visitor_id", "") or session_id)
            if not pages_by_session[session_id] or pages_by_session[session_id][-1] != path:
                pages_by_session[session_id].append(path)

        clicks = Counter()
        durations = defaultdict(list)
        scroll_depths = defaultdict(dict)
        for event in scope["events"].select_related("visit").order_by("-timestamp")[:30000]:
            path = _event_path(event)
            session_id = _event_session_id(event)
            payload = _safe_payload(event)
            if event.type == "click":
                clicks[path] += 1
            elif event.type == "time_on_page":
                duration = _payload_duration_seconds(event)
                if duration > 0:
                    durations[path].append(duration)
            elif event.type == "scroll_depth":
                depth = max(
                    _safe_int(payload.get("max_depth"), 0),
                    _safe_int(payload.get("current_depth"), 0),
                    _safe_int(payload.get("depth"), 0),
                )
                if depth > scroll_depths[path].get(session_id, 0):
                    scroll_depths[path][session_id] = min(depth, 100)

        exits = Counter()
        bounces = Counter()
        for path_list in pages_by_session.values():
            if not path_list:
                continue
            exits[path_list[-1]] += 1
            if len(path_list) == 1:
                bounces[path_list[0]] += 1

        leads_by_page = Counter()
        for lead in scope["leads"].only("source_url"):
            path = _pathname_from_url(getattr(lead, "source_url", "") or "")
            leads_by_page[path] += 1

        rows = []
        all_paths = set(views.keys()) | set(clicks.keys()) | set(leads_by_page.keys())
        for path in all_paths:
            view_count = views[path]
            duration_values = durations.get(path, [])
            scroll_values = list(scroll_depths.get(path, {}).values())
            leads = leads_by_page[path]
            rows.append(
                {
                    "path": path,
                    "views": view_count,
                    "unique_visitors": len(unique.get(path, set())),
                    "avg_time": round(sum(duration_values) / len(duration_values)) if duration_values else 0,
                    "avg_scroll_depth": round(sum(scroll_values) / len(scroll_values), 1) if scroll_values else 0,
                    "clicks": clicks[path],
                    "leads": leads,
                    "conversion": round((leads / view_count) * 100, 1) if view_count else 0,
                    "exits": exits[path],
                    "bounce_rate": round((bounces[path] / view_count) * 100, 1) if view_count else 0,
                }
            )
        rows.sort(key=lambda item: item["views"], reverse=True)
        return Response({"period": period, "pages": rows[:200]})


class AdminSiteAnalyticsErrorsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        error_types = {"error", "client_error", "js_error", "unhandled_rejection", "fetch_error"}
        rows = {}
        for event in scope["events"].filter(type__in=error_types).select_related("visit").order_by("-timestamp")[:10000]:
            payload = _safe_payload(event)
            message = str(payload.get("message") or payload.get("reason") or payload.get("name") or "Ошибка без сообщения")[:255]
            path = _event_path(event)
            key = (message, path, _event_browser(event), _event_device(event))
            row = rows.setdefault(
                key,
                {
                    "message": message,
                    "page": path,
                    "browser": _event_browser(event),
                    "device": _event_device(event),
                    "count": 0,
                    "last_seen": event.timestamp,
                    "stack": str(payload.get("stack") or "")[:1000],
                },
            )
            row["count"] += 1
            if event.timestamp > row["last_seen"]:
                row["last_seen"] = event.timestamp
        result = [{**row, "last_seen": _iso(row["last_seen"])} for row in rows.values()]
        result.sort(key=lambda item: item["count"], reverse=True)
        return Response({"period": period, "errors": result[:200]})


class AdminSiteAnalyticsPerformanceView(AdminSiteAnalyticsBaseView):
    METRIC_KEYS = {
        "lcp": ("lcp", "LCP"),
        "cls": ("cls", "CLS"),
        "inp": ("inp", "INP"),
        "fid": ("fid", "FID"),
        "ttfb": ("ttfb", "TTFB"),
        "page_load_time": ("page_load_time", "load_time", "loadTime"),
        "dom_content_loaded": ("dom_content_loaded", "domContentLoaded", "dcl"),
    }

    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        values = defaultdict(list)
        devices = defaultdict(lambda: defaultdict(list))
        poor_pages = Counter()
        for event in scope["events"].filter(type="performance").select_related("visit").order_by("-timestamp")[:10000]:
            payload = _safe_payload(event)
            metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else payload
            path = _event_path(event)
            device = _event_device(event)
            current = {}
            for metric, keys in self.METRIC_KEYS.items():
                value = 0.0
                for key in keys:
                    value = _safe_float(metrics.get(key), 0.0)
                    if value > 0:
                        break
                if value > 0:
                    values[metric].append(value)
                    devices[device][metric].append(value)
                    current[metric] = value
            if current.get("lcp", 0) > 2500 or current.get("cls", 0) > 0.1 or current.get("inp", 0) > 200 or current.get("page_load_time", 0) > 4000:
                poor_pages[path] += 1

        averages = {
            metric: round(sum(metric_values) / len(metric_values), 2) if metric_values else 0
            for metric, metric_values in values.items()
        }
        by_device = []
        for device, metric_map in devices.items():
            by_device.append(
                {
                    "device": device,
                    "metrics": {
                        metric: round(sum(metric_values) / len(metric_values), 2) if metric_values else 0
                        for metric, metric_values in metric_map.items()
                    },
                }
            )

        return Response(
            {
                "period": period,
                "samples": max((len(metric_values) for metric_values in values.values()), default=0),
                "averages": averages,
                "bad_pages": [{"path": path, "count": count} for path, count in poor_pages.most_common(30)],
                "devices": by_device,
            }
        )


class AdminSiteAnalyticsRecommendationsView(AdminSiteAnalyticsBaseView):
    def get(self, request, site_id: int):
        site, scope, period, _bounds = self.get_context(request, site_id)
        if site is None:
            return self.site_not_found()

        recommendations = []

        def add_recommendation(title, importance, reason, *, page="", description="", what_to_do="", related_sections=None):
            recommendations.append(
                {
                    "title": title,
                    "description": description,
                    "importance": importance,
                    "page": page,
                    "reason": reason,
                    "what_to_do": what_to_do,
                    "related_sections": related_sections or [],
                }
            )

        pageviews = scope["pageviews"].select_related("visit").order_by("-timestamp")[:30000]
        page_counts = Counter(_pageview_path(pageview) for pageview in pageviews)
        leads_by_page = Counter(_pathname_from_url(getattr(lead, "source_url", "") or "") for lead in scope["leads"].only("source_url"))

        for path, views_count in page_counts.most_common(20):
            if views_count >= 5 and leads_by_page[path] == 0:
                add_recommendation(
                    f"Страница {path} получает трафик, но не даёт заявок.",
                    "high" if views_count >= 20 else "medium",
                    f"{views_count} просмотров за период и 0 заявок.",
                    page=path,
                    description="Пользователи доходят до страницы, но не видят достаточно убедительного следующего шага.",
                    what_to_do="Добавьте заметную кнопку заявки, усилите оффер и проверьте, где пользователи кликают на этой странице.",
                    related_sections=["Страницы", "Тепловая карта", "Пути пользователей"],
                )

        scroll_values = []
        noninteractive_clicks = 0
        total_clicks = 0
        error_count = 0
        for event in scope["events"].select_related("visit").order_by("-timestamp")[:30000]:
            payload = _safe_payload(event)
            if event.type == "scroll_depth":
                scroll_values.append(
                    max(_safe_int(payload.get("max_depth"), 0), _safe_int(payload.get("current_depth"), 0), _safe_int(payload.get("depth"), 0))
                )
            elif event.type == "click":
                total_clicks += 1
                tag = str(payload.get("element_tag") or payload.get("tag") or "").lower()
                href = str(payload.get("element_href") or payload.get("href") or "")
                if tag and tag not in {"a", "button", "input", "select", "textarea"} and not href:
                    noninteractive_clicks += 1
            elif event.type in {"error", "client_error", "js_error", "unhandled_rejection", "fetch_error"}:
                error_count += 1

        avg_scroll = round(sum(scroll_values) / len(scroll_values), 1) if scroll_values else 0
        if avg_scroll and avg_scroll < 45:
            add_recommendation(
                "Пользователи редко доходят до середины страниц.",
                "medium",
                f"Средняя глубина прокрутки {avg_scroll}%.",
                description="Важные преимущества, контакты или форма могут находиться ниже зоны, которую видит большинство посетителей.",
                what_to_do="Перенесите ключевую кнопку, преимущества и форму выше, ближе к первому экрану.",
                related_sections=["Карта скроллинга", "Страницы"],
            )
        if total_clicks and noninteractive_clicks / total_clicks >= 0.25:
            add_recommendation(
                "Много кликов по неинтерактивным элементам.",
                "medium",
                f"{noninteractive_clicks} из {total_clicks} кликов пришлись на элементы без явного действия.",
                description="Пользователи могут считать картинки, блоки или текст кнопками. Это отвлекает от заявки.",
                what_to_do="Сделайте такие элементы ссылками или визуально уберите ощущение кликабельности.",
                related_sections=["Тепловая карта", "Записи сессий"],
            )
        if error_count:
            add_recommendation(
                "Есть клиентские ошибки на сайте.",
                "high" if error_count >= 10 else "medium",
                f"За период зафиксировано {error_count} ошибок.",
                description="Ошибки JavaScript или failed fetch могут мешать кнопкам, формам и отправке заявок.",
                what_to_do="Сначала исправьте ошибки на страницах с формами и высоким трафиком.",
                related_sections=["Ошибки", "Записи сессий"],
            )

        devices = _distribution_dict(scope["visits"], "device_type", allowed={"desktop", "mobile", "tablet", "unknown"})
        device_total = sum(devices.values())
        mobile_share = round((devices.get("mobile", 0) / device_total) * 100, 1) if device_total else 0
        if mobile_share >= 60:
            add_recommendation(
                "Высокая доля мобильных пользователей.",
                "medium",
                f"Мобильный трафик составляет {mobile_share}%. Проверьте формы и ключевые кнопки на телефоне.",
                description="Если большинство посетителей с телефона, неудобная мобильная форма напрямую снижает заявки.",
                what_to_do="Проверьте первый экран, размер кнопок, скорость и удобство заполнения формы на телефоне.",
                related_sections=["Обзор", "Производительность", "Записи сессий"],
            )

        if not recommendations:
            add_recommendation(
                "Критичных сигналов пока нет.",
                "low",
                "Данных недостаточно или показатели за выбранный период стабильны.",
                description="Продолжайте собирать данные и сравните показатели после новых посещений.",
                what_to_do="Проверьте установку трекера, выбранный период и вернитесь после накопления новых сессий.",
                related_sections=["Обзор", "Страницы"],
            )

        return Response({"period": period, "recommendations": recommendations[:20]})


def tracker_js_view(_request):
    script = r"""
(function() {
  const script = document.currentScript;
  const token = script && script.dataset ? (script.dataset.apiKey || '') : '';
  if (!token) return;
  const base = new URL(script.src).origin;
  const sessionKey = 'yadro_tracker_session';
  const visitorKey = 'yadro_tracker_visitor';
  const sessionId = sessionStorage.getItem(sessionKey) || (Date.now() + '-' + Math.random().toString(16).slice(2));
  const visitorId = localStorage.getItem(visitorKey) || (Date.now() + '-' + Math.random().toString(16).slice(2));
  sessionStorage.setItem(sessionKey, sessionId);
  localStorage.setItem(visitorKey, visitorId);
  const post = (path, payload) => fetch(base + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true
  }).catch(() => {});
  post('/api/track/visit-start/', { token, session_id: sessionId, visitor_id: visitorId, referrer: document.referrer || '' });
  post('/api/track/pageview/', { token, session_id: sessionId, visitor_id: visitorId, url: window.location.href, title: document.title || '' });
  document.addEventListener('click', function(e) {
    const node = e.target && e.target.closest ? e.target.closest('a,button,[role="button"]') : null;
    if (!node) return;
    post('/api/track/event/', { token, session_id: sessionId, visitor_id: visitorId, type: 'click', payload: { text: (node.innerText || '').trim().slice(0,120), id: node.id || '', class: node.className || '', path: window.location.pathname } });
  }, true);
  const started = Date.now();
  const onClose = () => {
    const duration = Math.max(0, Math.floor((Date.now() - started) / 1000));
    post('/api/track/event/', { token, session_id: sessionId, visitor_id: visitorId, type: 'time_on_page', payload: { path: window.location.pathname, duration_seconds: duration } });
    post('/api/track/visit-end/', { token, session_id: sessionId, visitor_id: visitorId, duration });
  };
  window.addEventListener('beforeunload', onClose);
  window.addEventListener('pagehide', onClose);
})();
"""
    return HttpResponse(script, content_type="application/javascript; charset=utf-8")
