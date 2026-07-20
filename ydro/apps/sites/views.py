from django.db.models import Count, Q
import json
import logging
import re
from html import escape
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from leads.services import send_telegram_message
from tracker.models import Site as TrackerSite
from subscriptions.access import FEATURE_LEADS, FEATURE_SITE_EDIT, FEATURE_TELEGRAM
from subscriptions.permissions import HasFeatureAccess

from .models import Site, SiteLead, SiteSection, WebsiteTemplate, WebsiteTemplateCategory
from .public_renderer import inject_subscription_lock, public_billing_url, site_requires_subscription_lock
from .preview import site_requires_preview_token, validate_site_preview_token
from .seo import build_public_site_seo, render_public_site_seo_head
from .serializers import (
    AdminLeadSerializer,
    AdminLeadStatusPatchSerializer,
    AdminMySiteSectionCreateSerializer,
    AdminMySiteSectionPatchSerializer,
    AdminMySiteSectionSerializer,
    AdminMySiteSerializer,
    WebsiteTemplateCategorySerializer,
    WebsiteTemplateCreateSiteSerializer,
    WebsiteTemplateCreatedSiteSerializer,
    WebsiteTemplateGenerateSerializer,
    WebsiteTemplateSerializer,
    PublicLeadCreateSerializer,
    PublicSiteSectionSerializer,
    PublicSiteSerializer,
    SiteRegenerateDesignSerializer,
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


def _inject_public_site_runtime(index_html, *, site, preview_mode, preview_token):
    runtime_json = json.dumps(
        {
            "slug": site.slug,
            "publicId": str(site.public_id),
            "preview": preview_mode,
            "token": preview_token if preview_mode else "",
        },
        ensure_ascii=True,
    ).replace("</", "<\\/")
    runtime_meta = f'<script>window.__TRACKNODE_SITE__ = {runtime_json};</script>'
    if re.search(r"</head\s*>", index_html, flags=re.IGNORECASE):
        return re.sub(r"</head\s*>", f"    {runtime_meta}\n  </head>", index_html, count=1, flags=re.IGNORECASE)
    return f"{runtime_meta}\n{index_html}"


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
        domain = _normalize_domain(request.query_params.get("domain"))
        if not domain:
            return Response({"detail": "Query param 'domain' is required."}, status=status.HTTP_400_BAD_REQUEST)

        site = (
            Site.objects.filter(is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .filter(domain__iexact=domain)
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
            Site.objects.filter(slug=self.kwargs["site_slug"])
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .first()
        )
        if site is None:
            raise NotFound(detail="Active site was not found.")
        preview_token_valid = validate_site_preview_token(site, request.query_params.get("token", ""))
        if (not site.is_active or site_requires_preview_token(site)) and not preview_token_valid:
            raise NotFound(detail="Active site was not found.")

        sections = SiteSection.objects.filter(site=site, is_active=True).order_by("order", "title")
        return Response(
            {
                "site": PublicSiteSerializer(site).data,
                "sections": PublicSiteSectionSerializer(sections, many=True).data,
            }
        )


@method_decorator(xframe_options_sameorigin, name="dispatch")
class PublicSiteHtmlView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        site = Site.objects.filter(slug=self.kwargs["site_slug"]).first()
        if site is None:
            raise NotFound(detail="Active site was not found.")

        preview_mode = request.query_params.get("preview") == "1"
        preview_token = request.query_params.get("token", "")
        if (not site.is_active or site_requires_preview_token(site)) and not (
            preview_mode and validate_site_preview_token(site, preview_token)
        ):
            raise NotFound(detail="Active site was not found.")

        index_html = _load_public_site_index_html()
        html = _inject_public_site_seo(index_html, build_public_site_seo(site))
        html = _inject_public_site_runtime(
            html,
            site=site,
            preview_mode=preview_mode,
            preview_token=preview_token,
        )
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

    def get_sites_queryset(self):
        base = Site.objects.all()
        if self.request.user.is_superuser:
            return base
        return base.filter(owner=self.request.user)

    def get_site(self):
        site_id = self.kwargs["site_id"]
        site = self.get_sites_queryset().filter(id=site_id).first()
        if site is None:
            raise NotFound(detail="Site was not found.")
        return site

    def get_user_leads_queryset(self):
        queryset = SiteLead.objects.select_related("site")
        if self.request.user.is_superuser:
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


class WebsiteTemplateCatalogView(APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def get(self, request):
        category_slug = request.query_params.get("category")
        categories = WebsiteTemplateCategory.objects.filter(is_active=True).order_by("sort_order", "name")
        templates = WebsiteTemplate.objects.filter(is_published=True, category__is_active=True).select_related("category", "source_site")
        if category_slug:
            templates = templates.filter(category__slug=category_slug)
        return Response(
            {
                "categories": WebsiteTemplateCategorySerializer(categories, many=True).data,
                "templates": WebsiteTemplateSerializer(
                    templates.order_by("sort_order", "name"),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class WebsiteTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def get(self, request, slug: str):
        template = get_object_or_404(
            WebsiteTemplate.objects.filter(is_published=True, category__is_active=True).select_related("category", "source_site"),
            slug=slug,
        )
        return Response(WebsiteTemplateSerializer(template).data, status=status.HTTP_200_OK)


class WebsiteTemplateCreateSiteView(APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def post(self, request, slug: str = ""):
        data = request.data.copy()
        if slug:
            data["template_slug"] = slug
        serializer = WebsiteTemplateCreateSiteSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            site = serializer.save()
        except serializers.ValidationError:
            raise
        except Exception:
            logger.exception("Unexpected website template clone failure template_slug=%s user_id=%s", slug, request.user.id)
            return Response(
                {
                    "code": "template_clone_failed",
                    "detail": "Ошибка сервера при создании сайта. Проверьте снимок шаблона и повторите попытку.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            WebsiteTemplateCreatedSiteSerializer(site, context={"template": serializer.context["template"]}).data,
            status=status.HTTP_201_CREATED,
        )


class WebsiteTemplateGenerateView(APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def post(self, request):
        serializer = WebsiteTemplateGenerateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            site = serializer.save()
        except serializers.ValidationError:
            raise
        except Exception:
            logger.exception("Unexpected website template generation failure user_id=%s", request.user.id)
            return Response(
                {
                    "code": "template_generation_failed",
                    "detail": "Ошибка сервера при создании сайта. Повторите попытку.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.to_representation(site), status=status.HTTP_201_CREATED)


class SiteRegenerateDesignView(APIView):
    permission_classes = [IsAuthenticated, HasFeatureAccess]
    required_feature = FEATURE_SITE_EDIT

    def post(self, request, site_id: int):
        sites = Site.objects.all() if request.user.is_superuser else Site.objects.filter(owner=request.user)
        site = sites.filter(id=site_id).first()
        if site is None:
            raise NotFound(detail="Site was not found.")
        serializer = SiteRegenerateDesignSerializer(data=request.data, context={"request": request, "site": site})
        serializer.is_valid(raise_exception=True)
        try:
            updated_site = serializer.save()
        except serializers.ValidationError:
            raise
        except Exception:
            logger.exception("Unexpected site design regeneration failure site_id=%s user_id=%s", site.id, request.user.id)
            return Response(
                {
                    "code": "design_regeneration_failed",
                    "detail": "Ошибка сервера при смене дизайна. Повторите попытку.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.to_representation(updated_site), status=status.HTTP_200_OK)


AdminWebsiteTemplateCatalogView = WebsiteTemplateCatalogView
AdminWebsiteTemplateCreateSiteView = WebsiteTemplateCreateSiteView


class AdminMySiteDetailView(AdminSiteAccessMixin, generics.RetrieveAPIView):
    serializer_class = AdminMySiteSerializer
    lookup_field = "id"
    lookup_url_kwarg = "site_id"

    def get_queryset(self):
        return self.get_sites_queryset().annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )


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
