import logging
import re
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from leads.services import send_telegram_message
from tracker.models import Site as TrackerSite
from subscriptions.access import FEATURE_ANALYTICS, FEATURE_LEADS, FEATURE_SITE_EDIT, FEATURE_TELEGRAM
from subscriptions.permissions import HasFeatureAccess
from platform_admin.permissions import is_platform_owner

from .models import Site, SiteLead, SiteSection
from .public_renderer import inject_subscription_lock, public_billing_url, site_requires_subscription_lock
from .seo import build_public_site_seo, render_public_site_seo_head
from .services import (
    ProtectedSiteError,
    ProtectedTemplateSourceError,
    SiteOperationConflict,
    SiteSnapshot,
    clear_site_analytics,
    delete_owned_site,
    filter_client_manageable_sites,
    is_technical_template_source_site,
    log_site_operation,
    technical_template_source_site_ids,
    website_template_for_source_site,
)
from .serializers import (
    AdminLeadSerializer,
    AdminLeadStatusPatchSerializer,
    AdminMySiteSectionCreateSerializer,
    AdminMySiteSectionPatchSerializer,
    AdminMySiteSectionSerializer,
    AdminMySiteSerializer,
    PublicLeadCreateSerializer,
    PublicSiteSectionSerializer,
    PublicSiteSerializer,
)
from .telegram_binding import build_site_start_payload
from .tracker_utils import build_tracker_script_tag

logger = logging.getLogger(__name__)


def _normalize_domain(value):
    if not value:
        return ""
    normalized = str(value).strip().lower()
    normalized = normalized.replace("http://", "").replace("https://", "")
    return normalized.strip("/")


def _domain_lookup_values(domain):
    normalized = _normalize_domain(domain)
    if not normalized:
        return []
    values = [normalized]
    if normalized.startswith("www."):
        values.append(normalized[4:])
    else:
        values.append(f"www.{normalized}")
    return values


_SEO_TITLE_RE = re.compile(r"\s*<title>.*?</title>", re.IGNORECASE | re.DOTALL)
_SEO_CANONICAL_RE = re.compile(
    r"\s*<link\b(?=[^>]*\brel=[\"']canonical[\"'])[^>]*>",
    re.IGNORECASE,
)
_SEO_JSON_LD_RE = re.compile(
    r"\s*<script\b(?=[^>]*\btype=[\"']application/ld\+json[\"'])[^>]*>.*?</script>",
    re.IGNORECASE | re.DOTALL,
)
_SEO_META_NAME_RE = re.compile(
    r"\s*<meta\b(?=[^>]*\bname=[\"']"
    r"(?:description|twitter:card|twitter:title|twitter:description|twitter:image)"
    r"[\"'])[^>]*>",
    re.IGNORECASE,
)
_SEO_META_PROPERTY_RE = re.compile(
    r"\s*<meta\b(?=[^>]*\bproperty=[\"']"
    r"(?:og:type|og:site_name|og:title|og:description|og:image|og:url)"
    r"[\"'])[^>]*>",
    re.IGNORECASE,
)


def _load_public_site_index_html():
    index_url = str(getattr(settings, "PUBLIC_SITE_STATIC_INDEX_URL", "") or "").strip()
    if index_url:
        try:
            with urlopen(index_url, timeout=2) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except (OSError, URLError, UnicodeDecodeError):
            pass

    return (
        "<!doctype html>\n"
        '<html lang="ru">\n'
        "  <head>\n"
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "  </head>\n"
        '  <body><div id="app"></div></body>\n'
        "</html>\n"
    )


def _inject_public_site_seo(index_html, seo):
    html = _SEO_TITLE_RE.sub("", index_html)
    html = _SEO_CANONICAL_RE.sub("", html)
    html = _SEO_JSON_LD_RE.sub("", html)
    html = _SEO_META_NAME_RE.sub("", html)
    html = _SEO_META_PROPERTY_RE.sub("", html)

    seo_head = render_public_site_seo_head(seo)
    if re.search(r"</head\s*>", html, flags=re.IGNORECASE):
        return re.sub(
            r"</head\s*>",
            f"    {seo_head}\n  </head>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return f"{seo_head}\n{html}"


class PublicSiteDetailView(generics.RetrieveAPIView):
    serializer_class = PublicSiteSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "slug"
    lookup_url_kwarg = "site_slug"

    def get_queryset(self):
        return Site.objects.filter(is_active=True).annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )


class PublicSiteSectionsListView(generics.ListAPIView):
    serializer_class = PublicSiteSectionSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return SiteSection.objects.filter(
            site__slug=self.kwargs["site_slug"],
            site__is_active=True,
            is_active=True,
        ).order_by("order", "title")


class PublicSiteSectionDetailView(generics.RetrieveAPIView):
    serializer_class = PublicSiteSectionSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "key"
    lookup_url_kwarg = "section_key"

    def get_queryset(self):
        return SiteSection.objects.filter(
            site__slug=self.kwargs["site_slug"],
            site__is_active=True,
            is_active=True,
        )


class PublicSiteByDomainView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        domains = _domain_lookup_values(request.query_params.get("domain"))
        if not domains:
            return Response({"detail": "Query param 'domain' is required."}, status=status.HTTP_400_BAD_REQUEST)

        site = (
            Site.objects.filter(is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .filter(domain__iexact=domains[0])
            .first()
        )
        if site is None and len(domains) > 1:
            site = (
                Site.objects.filter(is_active=True)
                .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
                .filter(domain__iexact=domains[1])
                .first()
            )

        if site is None:
            raise NotFound(detail="Active site for this domain was not found.")

        site_data = PublicSiteSerializer(site).data
        sections_data = PublicSiteSectionSerializer(
            SiteSection.objects.filter(site=site, is_active=True).order_by("order", "title"),
            many=True,
        ).data

        return Response({"site": site_data, "sections": sections_data})


class PublicSiteBundleBySlugView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        site = (
            Site.objects.filter(slug=self.kwargs["site_slug"], is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .first()
        )
        if site is None:
            raise NotFound(detail="Active site was not found.")

        sections = SiteSection.objects.filter(site=site, is_active=True).order_by("order", "title")
        return Response(
            {
                "site": PublicSiteSerializer(site).data,
                "sections": PublicSiteSectionSerializer(sections, many=True).data,
            }
        )


class PublicSiteHtmlView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        site = Site.objects.filter(slug=self.kwargs["site_slug"], is_active=True).first()
        if site is None:
            raise NotFound(detail="Active site was not found.")

        index_html = _load_public_site_index_html()
        html = _inject_public_site_seo(index_html, build_public_site_seo(site))
        subscription_required = site_requires_subscription_lock(site)
        if subscription_required:
            html = inject_subscription_lock(html, public_billing_url())
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["X-TrackNode-Site-Status"] = "suspended" if subscription_required else "active"
        response["X-TrackNode-Subscription-Required"] = str(subscription_required).lower()
        if subscription_required:
            response["X-TrackNode-Billing-Url"] = public_billing_url()
        response["Cache-Control"] = "no-store"
        return response


class PublicLeadCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "public_lead"

    def post(self, request, *args, **kwargs):
        serializer = PublicLeadCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Заполните обязательные поля", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(
                {"success": False, "message": "Сайт не найден", "errors": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "message": "Заявка успешно отправлена"}, status=status.HTTP_201_CREATED)


class PublicSiteLeadCreateBySlugView(PublicLeadCreateView):
    def post(self, request, *args, **kwargs):
        payload = request.data.copy()
        payload["site_slug"] = kwargs["site_slug"]
        serializer = PublicLeadCreateSerializer(data=payload, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Заполните обязательные поля", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(
                {"success": False, "message": "Сайт не найден", "errors": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "message": "Заявка успешно отправлена"}, status=status.HTTP_201_CREATED)


class AdminSiteAccessMixin:
    permission_classes = [IsAuthenticated]

    def has_global_site_access(self):
        return is_platform_owner(self.request.user)

    def get_sites_queryset(self):
        base = Site.objects.select_related("owner").all()
        if self.has_global_site_access():
            return filter_client_manageable_sites(base)
        return filter_client_manageable_sites(base.filter(owner=self.request.user))

    def get_sites_queryset_for_delete(self):
        base = Site.objects.select_related("owner").all()
        if self.has_global_site_access():
            return base
        return base.filter(owner=self.request.user)

    def get_site(self):
        site_id = self.kwargs["site_id"]
        site = self.get_sites_queryset().filter(id=site_id).first()
        if site is None:
            raise NotFound(detail="Site was not found.")
        return site

    def get_site_for_delete(self):
        site_id = self.kwargs["site_id"]
        site = self.get_sites_queryset_for_delete().filter(id=site_id).first()
        if site is None:
            raise NotFound(detail="Site was not found.")
        return site

    def get_user_leads_queryset(self):
        queryset = SiteLead.objects.select_related("site")
        source_ids = technical_template_source_site_ids()
        if source_ids:
            queryset = queryset.exclude(site_id__in=source_ids)
        if self.has_global_site_access():
            return queryset
        return queryset.filter(site__owner=self.request.user)


def _telegram_connect_data(site: Site) -> dict:
    payload = build_site_start_payload(site)
    bot_username = str(getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").lstrip("@")
    connect_url = f"https://t.me/{bot_username}?start={payload}" if bot_username else ""
    return {
        "connect_token": payload,
        "start_command": f"/start {payload}",
        "telegram_bot_username": bot_username,
        "telegram_connect_url": connect_url,
    }


class AdminSiteTelegramStatusView(AdminSiteAccessMixin, APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_TELEGRAM

    def get(self, request, site_id: int):
        site = self.get_site()
        connected = bool(site.telegram_chat_id and site.send_to_telegram)
        delivery_mode = str(getattr(settings, "TELEGRAM_DELIVERY_MODE", "direct") or "").strip().lower()
        if delivery_mode == "relay":
            bot_configured = bool(getattr(settings, "TELEGRAM_RELAY_URL", "") and getattr(settings, "TELEGRAM_RELAY_TOKEN", ""))
        else:
            bot_configured = bool(getattr(settings, "TELEGRAM_BOT_TOKEN", ""))
        data = {
            "connected": connected,
            "telegram_status": "connected" if connected else "disconnected",
            "send_to_telegram": bool(site.send_to_telegram),
            "chat_id": site.telegram_chat_id or "",
            "connected_at": site.telegram_connected_at,
            "bot_configured": bot_configured,
        }
        data.update(_telegram_connect_data(site))
        return Response(data, status=status.HTTP_200_OK)


class AdminSiteTelegramDisconnectView(AdminSiteAccessMixin, APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_TELEGRAM

    def post(self, request, site_id: int):
        site = self.get_site()
        if not site.telegram_chat_id and not site.send_to_telegram:
            return Response({"ok": True, "detail": "Telegram уже отключен."}, status=status.HTTP_200_OK)

        site.telegram_chat_id = None
        site.send_to_telegram = False
        site.telegram_connected_at = None
        site.save(update_fields=["telegram_chat_id", "send_to_telegram", "telegram_connected_at", "updated_at"])
        return Response({"ok": True, "detail": "Telegram отключен."}, status=status.HTTP_200_OK)


class AdminSiteTelegramSendTestView(AdminSiteAccessMixin, APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_TELEGRAM

    def post(self, request, site_id: int):
        site = self.get_site()
        if not site.telegram_chat_id or not site.send_to_telegram:
            return Response(
                {
                    "ok": False,
                    "detail": "Telegram пока не подключен. Нажмите «Подключить Telegram» и отправьте команду /start боту.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_text = (
            "Тестовое сообщение из Yadro\n\n"
            f"Сайт: {site.name}\n"
            f"Домен: {site.domain or site.slug}\n"
            f"Дата: {timezone.localtime(timezone.now()):%d.%m.%Y %H:%M}"
        )
        delivered = send_telegram_message(site.telegram_chat_id, test_text)
        if delivered:
            return Response({"ok": True, "detail": "Тестовое сообщение отправлено."}, status=status.HTTP_200_OK)

        return Response(
            {
                "ok": False,
                "detail": "Не удалось отправить сообщение в Telegram. Проверьте токен бота и повторите подключение.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )


class AdminSiteTrackingKeyRefreshView(AdminSiteAccessMixin, APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def post(self, request, site_id: int):
        site = self.get_site()
        old_api_key = site.api_key
        new_api_key = Site._meta.get_field("api_key").default()
        domain_value = site.domain or site.slug or site.name

        with transaction.atomic():
            site.api_key = new_api_key
            site.save(update_fields=["api_key", "updated_at"])

            tracker_site = TrackerSite.objects.filter(token=old_api_key).first()
            if tracker_site is not None:
                tracker_site.token = new_api_key
                tracker_site.domain = domain_value
                tracker_site.is_active = True
                tracker_site.save(update_fields=["token", "domain", "is_active"])
            else:
                TrackerSite.objects.update_or_create(
                    token=new_api_key,
                    defaults={"domain": domain_value, "is_active": True},
                )
        return Response(
            {
                "ok": True,
                "api_key": site.api_key,
                "tracker_script_tag": build_tracker_script_tag(site.api_key),
                "detail": "Ключ аналитики обновлен.",
            },
            status=status.HTTP_200_OK,
        )


class AdminMySitesListView(AdminSiteAccessMixin, generics.ListAPIView):
    serializer_class = AdminMySiteSerializer

    def get_queryset(self):
        return self.get_sites_queryset().annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        ).order_by("id")


class AdminMySiteDetailView(AdminSiteAccessMixin, generics.RetrieveAPIView):
    serializer_class = AdminMySiteSerializer
    lookup_field = "id"
    lookup_url_kwarg = "site_id"
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        return self.get_sites_queryset().annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )

    def get(self, request, *args, **kwargs):
        site = self.get_sites_queryset_for_delete().filter(id=self.kwargs["site_id"]).first()
        if site is not None and is_technical_template_source_site(site):
            if not self.has_global_site_access():
                raise NotFound(detail="Site was not found.")
            return Response(
                {
                    "code": "protected_template_source",
                    "detail": "Источник шаблона управляется через каталог шаблонов.",
                    "template_source": website_template_for_source_site(site.id),
                    "platform_url": f"/platform/sites/{site.id}",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        site = self.get_site()
        serializer = self.get_serializer(site)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        site = self.get_site_for_delete()
        snapshot = SiteSnapshot.from_site(site)
        if is_technical_template_source_site(site):
            if not self.has_global_site_access():
                raise NotFound(detail="Site was not found.")
            detail = "Источник шаблона управляется через каталог шаблонов."
            log_site_operation(
                request,
                site=site,
                snapshot=snapshot,
                action="site.delete",
                result="blocked",
                error=detail,
            )
            return Response(
                {"code": "protected_template_source", "detail": detail},
                status=status.HTTP_403_FORBIDDEN,
            )

        confirmation = str(request.data.get("confirmation") or "").strip()
        if confirmation != site.name:
            return Response(
                {
                    "code": "invalid_confirmation",
                    "detail": "Введите точное название сайта для подтверждения удаления.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = delete_owned_site(site=site, request=request)
        except ProtectedTemplateSourceError as exc:
            log_site_operation(
                request,
                site=site,
                snapshot=snapshot,
                action="site.delete",
                result="blocked",
                error=str(exc),
            )
            return Response(
                {"code": "protected_template_source", "detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ProtectedSiteError as exc:
            log_site_operation(
                request,
                site=site,
                snapshot=snapshot,
                action="site.delete",
                result="blocked",
                error=str(exc),
            )
            return Response({"code": "protected_site", "detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except SiteOperationConflict as exc:
            log_site_operation(
                request,
                site=site,
                snapshot=snapshot,
                action="site.delete",
                result="conflict",
                error=str(exc),
            )
            return Response({"code": "site_has_active_jobs", "detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError as exc:
            logger.exception(
                "site.delete dependency conflict endpoint=%s user_id=%s site_id=%s snapshot=%s stage=delete_owned_site error=%s",
                request.path,
                getattr(request.user, "id", None),
                snapshot.id,
                {
                    "site_id": snapshot.id,
                    "site_name": snapshot.name,
                    "site_slug": snapshot.slug,
                    "domain": snapshot.domain,
                    "owner_id": snapshot.owner_id,
                },
                str(exc),
            )
            return Response(
                {
                    "code": "site_has_dependencies",
                    "detail": "Сайт связан с другими объектами и пока не может быть удалён.",
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception:
            logger.exception(
                "site.delete unexpected error endpoint=%s user_id=%s site_id=%s snapshot=%s stage=delete_owned_site",
                request.path,
                getattr(request.user, "id", None),
                snapshot.id,
                {
                    "site_id": snapshot.id,
                    "site_name": snapshot.name,
                    "site_slug": snapshot.slug,
                    "domain": snapshot.domain,
                    "owner_id": snapshot.owner_id,
                },
            )
            raise

        return Response(result, status=status.HTTP_200_OK)


class AdminMySiteAnalyticsClearView(AdminSiteAccessMixin, APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_ANALYTICS

    def delete(self, request, site_id: int):
        site = self.get_site()
        confirmation = str(request.data.get("confirmation") or "").strip()
        if confirmation not in {site.name, "ОЧИСТИТЬ"}:
            return Response(
                {
                    "code": "invalid_confirmation",
                    "detail": "Для очистки аналитики введите название сайта или ОЧИСТИТЬ.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        snapshot = SiteSnapshot.from_site(site)
        try:
            result = clear_site_analytics(site=site, request=request)
        except SiteOperationConflict as exc:
            log_site_operation(
                request,
                site=site,
                snapshot=snapshot,
                action="site.analytics.clear",
                result="conflict",
                error=str(exc),
            )
            return Response({"code": "site_has_active_jobs", "detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_200_OK)


class AdminMySiteSectionsListCreateView(AdminSiteAccessMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_site()).order_by("order", "title")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminMySiteSectionCreateSerializer
        return AdminMySiteSectionSerializer

    def perform_create(self, serializer):
        serializer.save(site=self.get_site())


class AdminMySiteSectionDetailView(AdminSiteAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_site())

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, id=self.kwargs["section_id"])

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AdminMySiteSectionPatchSerializer
        return AdminMySiteSectionSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMyLeadsListView(AdminSiteAccessMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_LEADS

    serializer_class = AdminLeadSerializer

    def get_queryset(self):
        queryset = self.get_user_leads_queryset().order_by("-created_at")
        site_id = self.request.query_params.get("site_id")
        status_value = self.request.query_params.get("status")

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset


class AdminMyLeadDetailView(AdminSiteAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_LEADS

    serializer_class = AdminLeadSerializer
    lookup_url_kwarg = "lead_id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return self.get_user_leads_queryset()

    def get_serializer_class(self):
        if self.request.method.lower() == "patch":
            return AdminLeadStatusPatchSerializer
        return AdminLeadSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AdminLeadStatusPatchSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminLeadSerializer(instance).data, status=status.HTTP_200_OK)
