from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Max, Q, Subquery, OuterRef, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_recommendations.client import AIRecommendationsClient, AIServiceError
from ai_recommendations.models import AIRecommendationJob
from ai_recommendations.tasks import sync_job
from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.sites.models import Site, SiteLead
from clients.models import Client
from seo_audit.models import SiteSEOAudit
from subscriptions.models import Subscription

from platform_admin.models import PlatformAuditLog
from platform_admin.pagination import PlatformPagination
from platform_admin.permissions import CanManagePlatformRecommendations, CanViewPlatformPersonalData, IsPlatformOwner
from platform_admin.services import audit, period_bounds

ERROR_TYPES = ("error", "client_error", "js_error", "unhandled_rejection", "fetch_error")


class PlatformView(APIView):
    permission_classes = (IsAuthenticated, IsPlatformOwner)


def _site_filter(request, queryset):
    search = request.query_params.get("search", "").strip()
    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(domain__icontains=search) | Q(slug__icontains=search) | Q(owner__username__icontains=search) | Q(owner__email__icontains=search))
    if request.query_params.get("active") in {"true", "false"}:
        queryset = queryset.filter(is_active=request.query_params["active"] == "true")
    owner = request.query_params.get("owner")
    if owner: queryset = queryset.filter(owner_id=owner)
    plan = request.query_params.get("plan")
    if plan: queryset = queryset.filter(owner__client__subscriptions__plan__slug=plan)
    subscription_status = request.query_params.get("subscription_status")
    if subscription_status: queryset = queryset.filter(owner__client__subscriptions__status=subscription_status)
    return queryset


def _annotated_sites(request):
    start, end = period_bounds(request)
    event_filter = Q(visits__events__timestamp__range=(start, end), visits__events__type__in=ERROR_TYPES)
    queryset = _site_filter(request, Site.objects.select_related("owner", "owner__client_profile")).annotate(
        visits_period=Count("visits", filter=Q(visits__started_at__range=(start, end), visits__is_bot=False), distinct=True),
        unique_visitors=Count("visits__visitor_id", filter=Q(visits__started_at__range=(start, end), visits__is_bot=False) & ~Q(visits__visitor_id=""), distinct=True),
        page_views=Count("visits__pageviews", filter=Q(visits__pageviews__timestamp__range=(start, end), visits__is_bot=False), distinct=True),
        leads_period=Count("leads", filter=Q(leads__created_at__range=(start, end)), distinct=True),
        errors_period=Count("visits__events", filter=event_filter, distinct=True),
        last_event_at=Max("visits__events__timestamp"), last_lead_at=Max("leads__created_at"),
    )
    traffic = request.query_params.get("traffic")
    if traffic == "yes": queryset = queryset.filter(visits_period__gt=0)
    elif traffic == "no": queryset = queryset.filter(visits_period=0)
    errors = request.query_params.get("errors")
    if errors == "yes": queryset = queryset.filter(errors_period__gt=0)
    elif errors == "no": queryset = queryset.filter(errors_period=0)
    ordering = request.query_params.get("ordering", "-visits_period")
    allowed = {"name", "domain", "created_at", "visits_period", "unique_visitors", "page_views", "leads_period", "errors_period", "last_event_at", "last_lead_at"}
    raw = ordering.lstrip("-")
    return queryset.order_by(ordering if raw in allowed else "-visits_period"), start, end


def _subscription_map(owner_ids):
    clients = {item.owner_id: item for item in Client.objects.filter(owner_id__in=owner_ids)}
    subscriptions = {}
    for item in Subscription.objects.filter(client_id__in=[c.id for c in clients.values()]).select_related("plan").order_by("client_id", "-updated_at"):
        subscriptions.setdefault(item.client_id, item)
    return clients, subscriptions


def _site_rows(sites):
    clients, subscriptions = _subscription_map([site.owner_id for site in sites])
    rows = []
    for site in sites:
        client = clients.get(site.owner_id); subscription = subscriptions.get(getattr(client, "id", None))
        rows.append({"id": site.id, "name": site.name, "domain": site.domain, "slug": site.slug, "owner_id": site.owner_id, "owner": site.owner.get_full_name() or site.owner.username, "owner_email": site.owner.email, "is_active": site.is_active, "created_at": site.created_at, "plan": getattr(getattr(subscription, "plan", None), "name", ""), "plan_slug": getattr(getattr(subscription, "plan", None), "slug", ""), "subscription_status": getattr(subscription, "status", "none"), "paid_until": getattr(subscription, "paid_until", None), "visits": site.visits_period, "unique_visitors": site.unique_visitors, "page_views": site.page_views, "leads": site.leads_period, "conversion": round(site.leads_period / site.visits_period * 100, 2) if site.visits_period else 0, "errors": site.errors_period, "last_event_at": site.last_event_at, "last_lead_at": site.last_lead_at})
    return rows


class OverviewView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request); today = timezone.localdate()
        visits = Visit.objects.filter(started_at__range=(start, end), is_bot=False)
        sites = Site.objects.all(); subscriptions = Subscription.objects.all()
        sites_with_traffic = visits.values("site_id").distinct()
        errors = TrackingEvent.objects.filter(timestamp__range=(start, end), type__in=ERROR_TYPES)
        ai_jobs = AIRecommendationJob.objects.filter(created_at__range=(start, end), deleted_at__isnull=True)
        critical = sum(1 for result in ai_jobs.exclude(result=None).values_list("result", flat=True) for item in (result or {}).get("recommendations", []) if item.get("priority") in {"very_important", "critical"})
        attention = []
        for site in sites.exclude(id__in=sites_with_traffic).order_by("-created_at")[:10]:
            reason = "Сайт новый или пока получает мало посещений — стоит проверить подключение после накопления данных." if site.created_at >= timezone.now() - timedelta(days=14) else "За выбранный период посещения не зафиксированы."
            attention.append({"site_id": site.id, "site_name": site.name, "reason": reason, "kind": "no_traffic"})
        expiring = list(subscriptions.filter(paid_until__lte=timezone.now() + timedelta(days=7)).select_related("client__owner")[:10])
        expiring_sites = {site.owner_id: site for site in Site.objects.filter(owner_id__in=[item.client.owner_id for item in expiring]).order_by("owner_id", "id")}
        for subscription in expiring:
            site = expiring_sites.get(subscription.client.owner_id)
            if site: attention.append({"site_id": site.id, "site_name": site.name, "reason": "Срок подписки заканчивается или уже истёк.", "kind": "subscription"})
        return Response({"period": {"date_from": start.date(), "date_to": end.date()}, "metrics": {"clients_total": Client.objects.count(), "clients_active": Client.objects.filter(is_active=True).count(), "sites_total": sites.count(), "sites_active": sites.filter(is_active=True).count(), "sites_without_traffic": sites.exclude(id__in=sites_with_traffic).count(), "sites_with_errors": errors.values("visit__site_id").distinct().count(), "visits": visits.count(), "unique_visitors": visits.exclude(visitor_id="").values("site_id", "visitor_id").distinct().count(), "page_views": PageView.objects.filter(timestamp__range=(start, end), visit__is_bot=False).count(), "leads_total": SiteLead.objects.count(), "leads_today": SiteLead.objects.filter(created_at__date=today).count(), "leads_period": SiteLead.objects.filter(created_at__range=(start, end)).count(), "subscriptions_active": subscriptions.filter(status=Subscription.Status.ACTIVE, paid_until__gt=timezone.now()).count(), "subscriptions_trial": subscriptions.filter(is_trial=True, paid_until__gt=timezone.now()).count(), "subscriptions_expired": subscriptions.filter(Q(status=Subscription.Status.EXPIRED) | Q(paid_until__lte=timezone.now())).count(), "recommendations": ai_jobs.count(), "critical_recommendations": critical}, "attention": attention[:20]})


class SitesView(PlatformView):
    def get(self, request):
        queryset, start, end = _annotated_sites(request)
        paginator = PlatformPagination(); page = paginator.paginate_queryset(queryset, request)
        response = paginator.get_paginated_response(_site_rows(page))
        response.data["period"] = {"date_from": start.date(), "date_to": end.date()}
        return response


class SiteDetailView(PlatformView):
    def get(self, request, site_id):
        queryset, start, end = _annotated_sites(request)
        site = queryset.filter(id=site_id).first()
        if not site: return Response({"detail": "Сайт не найден."}, status=404)
        row = _site_rows([site])[0]
        row["tracker_key"] = site.api_key if request.user.has_perm("platform_admin.view_platform_tracker_key") else None
        row["permissions"] = {"view_tracker_key": request.user.has_perm("platform_admin.view_platform_tracker_key")}
        row["latest_leads"] = list(SiteLead.objects.filter(site=site).values("id", "name", "status", "created_at")[:10])
        row["seo_audits"] = list(SiteSEOAudit.objects.filter(domain__iexact=site.domain).values("id", "status", "seo_score", "created_at", "finished_at")[:10])
        row["recommendations"] = list(AIRecommendationJob.objects.filter(site=site, deleted_at__isnull=True).values("id", "recommendation_type", "status", "period_from", "period_to", "created_at")[:20])
        row["view_as_owner"] = {"enabled": True, "read_only": True, "owner_id": site.owner_id}
        return Response(row)


class AnalyticsView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request); visits = Visit.objects.filter(started_at__range=(start, end), is_bot=False)
        site_id, owner_id = request.query_params.get("site"), request.query_params.get("owner")
        if site_id: visits = visits.filter(site_id=site_id)
        if owner_id: visits = visits.filter(site__owner_id=owner_id)
        site_ids = visits.values_list("site_id", flat=True)
        pages = PageView.objects.filter(timestamp__range=(start, end), visit__in=visits)
        events = TrackingEvent.objects.filter(timestamp__range=(start, end), visit__in=visits)
        leads = SiteLead.objects.filter(created_at__range=(start, end), site_id__in=site_ids)
        daily = visits.annotate(day=TruncDate("started_at")).values("day").annotate(visits=Count("id"), unique=Count("visitor_id", distinct=True)).order_by("day")
        sources = visits.values("referrer").annotate(count=Count("id")).order_by("-count")[:15]
        popular = visits.values("site_id", "site__name").annotate(visits=Count("id")).order_by("-visits")[:15]
        visit_count, lead_count = visits.count(), leads.count()
        return Response({"period": {"date_from": start.date(), "date_to": end.date()}, "totals": {"visits": visit_count, "unique_visitors": visits.exclude(visitor_id="").values("site_id", "visitor_id").distinct().count(), "page_views": pages.count(), "leads": lead_count, "events": events.count(), "conversion": round(lead_count / visit_count * 100, 2) if visit_count else 0, "errors": events.filter(type__in=ERROR_TYPES).count()}, "daily": list(daily), "sources": list(sources), "popular_sites": list(popular), "sites_without_traffic": list(Site.objects.exclude(id__in=site_ids).values("id", "name")[:50])})


class ClientsView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request); users = get_user_model().objects.select_related("client_profile").annotate(sites_count=Count("sites", distinct=True), visits_period=Count("sites__visits", filter=Q(sites__visits__started_at__range=(start, end), sites__visits__is_bot=False), distinct=True), leads_period=Count("sites__leads", filter=Q(sites__leads__created_at__range=(start, end)), distinct=True)).order_by("-date_joined")
        search = request.query_params.get("search", "").strip()
        if search: users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(client_profile__company_name__icontains=search))
        paginator = PlatformPagination(); page = paginator.paginate_queryset(users, request)
        clients, subscriptions = _subscription_map([user.id for user in page]); data = []
        for user in page:
            client = clients.get(user.id); subscription = subscriptions.get(getattr(client, "id", None)); profile = getattr(user, "client_profile", None)
            data.append({"id": user.id, "username": user.username, "email": user.email, "company": getattr(profile, "company_name", ""), "sites_count": user.sites_count, "visits": user.visits_period, "leads": user.leads_period, "date_joined": user.date_joined, "last_login": user.last_login, "plan": getattr(getattr(subscription, "plan", None), "name", ""), "subscription_status": getattr(subscription, "status", "none"), "paid_until": getattr(subscription, "paid_until", None)})
        return paginator.get_paginated_response(data)


class ClientDetailView(PlatformView):
    def get(self, request, client_id):
        user = get_user_model().objects.select_related("client_profile").filter(id=client_id).first()
        if not user: return Response({"detail": "Клиент не найден."}, status=404)
        return Response({"id": user.id, "username": user.username, "email": user.email, "company": getattr(getattr(user, "client_profile", None), "company_name", ""), "date_joined": user.date_joined, "last_login": user.last_login, "sites": list(user.sites.values("id", "name", "domain", "is_active", "created_at"))})


class LeadsView(PlatformView):
    permission_classes = (IsAuthenticated, IsPlatformOwner, CanViewPlatformPersonalData)
    def get(self, request):
        start, end = period_bounds(request); queryset = SiteLead.objects.select_related("site", "site__owner").filter(created_at__range=(start, end))
        for key, field in (("site", "site_id"), ("owner", "site__owner_id"), ("status", "status")):
            if request.query_params.get(key): queryset = queryset.filter(**{field: request.query_params[key]})
        source = request.query_params.get("source");
        if source: queryset = queryset.filter(source_url__icontains=source)
        paginator = PlatformPagination(); page = paginator.paginate_queryset(queryset.order_by("-created_at"), request)
        audit(request, "view_leads_personal_data", object_type="lead_list", metadata={"count": len(page)})
        return paginator.get_paginated_response([{"id": lead.id, "site_id": lead.site_id, "site": lead.site.name, "owner": lead.site.owner.get_full_name() or lead.site.owner.username, "created_at": lead.created_at, "name": lead.name, "phone": lead.phone, "email": lead.email, "source": lead.source_url, "page": lead.source_url, "status": lead.status} for lead in page])


class RecommendationsView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request); queryset = AIRecommendationJob.objects.select_related("site", "site__owner").filter(created_at__range=(start, end), deleted_at__isnull=True)
        if request.query_params.get("hidden") != "all": queryset = queryset.filter(platform_hidden_at__isnull=True)
        for key, field in (("site", "site_id"), ("status", "status"), ("type", "recommendation_type")):
            if request.query_params.get(key): queryset = queryset.filter(**{field: request.query_params[key]})
        paginator = PlatformPagination(); page = paginator.paginate_queryset(queryset, request); rows = []
        for job in page:
            recommendations = (job.result or {}).get("recommendations", [])
            rows.append({"id": job.id, "site_id": job.site_id, "site": job.site.name, "owner": job.site.owner.get_full_name() or job.site.owner.username, "created_at": job.created_at, "type": job.recommendation_type, "status": job.status, "period_from": job.period_from, "period_to": job.period_to, "has_analytics": bool((job.input_snapshot or {}).get("analytics")), "has_seo": bool((job.input_snapshot or {}).get("seo")), "title": recommendations[0].get("title", "") if recommendations else "", "priority": recommendations[0].get("priority", "") if recommendations else "", "hidden": bool(job.platform_hidden_at), "reviewed": bool(job.platform_reviewed_at)})
        return paginator.get_paginated_response(rows)


class RecommendationDetailView(PlatformView):
    permission_classes = (IsAuthenticated, IsPlatformOwner, CanManagePlatformRecommendations)
    def get_job(self, job_id): return AIRecommendationJob.objects.select_related("site", "site__owner").filter(id=job_id).first()
    def get(self, request, job_id):
        job = self.get_job(job_id)
        if not job: return Response({"detail": "Рекомендация не найдена."}, status=404)
        audit(request, "view_ai_technical_data", site=job.site, object_type="ai_job", object_id=job.id)
        return Response({"id": job.id, "site": {"id": job.site_id, "name": job.site.name, "owner": job.site.owner.email}, "status": job.status, "period": {"date_from": job.period_from, "date_to": job.period_to}, "created_at": job.created_at, "started_at": job.started_at, "completed_at": job.completed_at, "input_snapshot": job.input_snapshot, "technical_result": job.result, "error": job.error_message, "poll_attempts": job.poll_attempts, "model": job.openai_model or None, "prompt_version": job.prompt_version, "input_tokens": job.input_tokens, "output_tokens": job.output_tokens, "has_analytics": bool((job.input_snapshot or {}).get("analytics")), "has_seo": bool((job.input_snapshot or {}).get("seo")), "reviewed_at": job.platform_reviewed_at, "hidden_at": job.platform_hidden_at})
    def post(self, request, job_id):
        job = self.get_job(job_id)
        if not job: return Response({"detail": "Рекомендация не найдена."}, status=404)
        action = request.data.get("action")
        if action == "retry":
            if job.status != job.Status.FAILED: return Response({"detail": "Повторить можно только задание с ошибкой."}, status=409)
            try: remote = AIRecommendationsClient().retry_job(job.remote_job_id)
            except AIServiceError as exc: return Response({"detail": str(exc)}, status=502)
            job.status, job.error_message = remote["status"], ""; job.save(); sync_job.delay(str(job.id)); audit(request, "retry_ai_recommendation", site=job.site, object_type="ai_job", object_id=job.id)
        elif action == "hide":
            job.platform_hidden_at = timezone.now(); job.save(update_fields=("platform_hidden_at", "updated_at")); audit(request, "hide_ai_recommendation", site=job.site, object_type="ai_job", object_id=job.id)
        elif action == "reviewed":
            job.platform_reviewed_at = timezone.now(); job.save(update_fields=("platform_reviewed_at", "updated_at")); audit(request, "review_ai_recommendation", site=job.site, object_type="ai_job", object_id=job.id)
        else: return Response({"detail": "Неизвестное действие."}, status=400)
        return Response({"status": job.status, "action": action})


class HealthView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request)
        return Response({"status": "ok", "period": {"date_from": start.date(), "date_to": end.date()}, "sites": Site.objects.count(), "active_sites": Site.objects.filter(is_active=True).count(), "sites_with_recent_events": TrackingEvent.objects.filter(timestamp__range=(start, end)).values("visit__site_id").distinct().count(), "errors": TrackingEvent.objects.filter(timestamp__range=(start, end), type__in=ERROR_TYPES).count()})


class AuditLogView(PlatformView):
    def get(self, request):
        paginator = PlatformPagination(); queryset = PlatformAuditLog.objects.select_related("actor", "site").all(); page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([{"id": row.id, "created_at": row.created_at, "actor": row.actor.username, "action": row.action, "site": getattr(row.site, "name", None), "object_type": row.object_type, "object_id": row.object_id, "ip_address": row.ip_address, "metadata": row.metadata} for row in page])


class SEOAuditsView(PlatformView):
    def get(self, request):
        start, end = period_bounds(request); queryset = SiteSEOAudit.objects.select_related("client", "client__owner").filter(created_at__range=(start, end))
        status_filter = request.query_params.get("status")
        if status_filter: queryset = queryset.filter(status=status_filter)
        search = request.query_params.get("search", "").strip()
        if search: queryset = queryset.filter(Q(domain__icontains=search) | Q(client__owner__email__icontains=search))
        paginator = PlatformPagination(); page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([{"id": item.id, "domain": item.domain, "owner": item.client.owner.email, "status": item.status, "score": item.seo_score, "pages": item.pages_count, "problems": item.pages_with_speed_issues + item.pages_with_indexing_issues, "created_at": item.created_at, "finished_at": item.finished_at} for item in page])


class SubscriptionsView(PlatformView):
    def get(self, request):
        queryset = Subscription.objects.select_related("client", "client__owner", "plan").order_by("-updated_at")
        status_filter = request.query_params.get("status")
        if status_filter: queryset = queryset.filter(status=status_filter)
        search = request.query_params.get("search", "").strip()
        if search: queryset = queryset.filter(Q(client__name__icontains=search) | Q(client__owner__email__icontains=search) | Q(plan__name__icontains=search))
        paginator = PlatformPagination(); page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([{"id": item.id, "client": item.client.name, "owner": item.client.owner.email, "plan": getattr(item.plan, "name", ""), "status": item.status, "is_trial": item.is_trial, "paid_until": item.paid_until, "auto_renew": item.auto_renew, "updated_at": item.updated_at} for item in page])
