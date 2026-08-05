from django.conf import settings
from django.utils import timezone

from clients.models import Client
from clients.services import get_or_create_client_for_site, get_user_client
from platform_admin.permissions import is_platform_owner
from subscriptions.models import Subscription, SubscriptionPayment


PLAN_CONTENT_HOSTING = "content_hosting"
PLAN_BUSINESS_ANALYTICS = "business_analytics"

FEATURE_DASHBOARD_OVERVIEW = "dashboard_overview"
FEATURE_SITE_EDIT = "site_edit"
FEATURE_LEADS = "leads"
FEATURE_NOTIFICATIONS = "notifications"
FEATURE_ANALYTICS = "analytics"
FEATURE_SEO_AUDIT = "seo_audit"
FEATURE_COMPETITORS = "competitors"
FEATURE_TELEGRAM = "telegram"
FEATURE_REPORTS = "reports"
FEATURE_HEATMAPS = "heatmaps"
FEATURE_SESSION_RECORDINGS = "session_recordings"
FEATURE_AI_RECOMMENDATIONS = "ai_recommendations"
FEATURE_BILLING = "billing"
FEATURE_BILLING_FULL_ACCESS = "billing_full_access"

BASE_FEATURES = (
    FEATURE_DASHBOARD_OVERVIEW,
    FEATURE_NOTIFICATIONS,
    FEATURE_BILLING,
)
CONTENT_HOSTING_FEATURES = (
    *BASE_FEATURES,
    FEATURE_SITE_EDIT,
    FEATURE_LEADS,
)
BUSINESS_ANALYTICS_FEATURES = (
    *CONTENT_HOSTING_FEATURES,
    FEATURE_ANALYTICS,
    FEATURE_SEO_AUDIT,
    FEATURE_COMPETITORS,
    FEATURE_TELEGRAM,
    FEATURE_REPORTS,
    FEATURE_HEATMAPS,
    FEATURE_SESSION_RECORDINGS,
    FEATURE_AI_RECOMMENDATIONS,
    FEATURE_BILLING_FULL_ACCESS,
)
BUSINESS_ONLY_FEATURES = frozenset(BUSINESS_ANALYTICS_FEATURES) - frozenset(CONTENT_HOSTING_FEATURES)

BUSINESS_ANALYTICS_REQUIRED_MESSAGE = "Функция доступна на тарифе Бизнес-аналитика"
ACTIVE_PLAN_REQUIRED_MESSAGE = "Для доступа к функции подключите тариф"


def billing_is_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_BILLING", False))


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_superuser_client(request=None):
    requested_id = None
    if request is not None:
        requested_id = (
            getattr(request, "query_params", {}).get("client_id")
            or getattr(request, "data", {}).get("client_id")
            or request.headers.get("X-Client-Id")
        )

    client_id = _safe_int(requested_id)
    if client_id:
        client = Client.objects.filter(id=client_id, is_active=True).first()
        if client is not None:
            return client

    return Client.objects.filter(is_active=True).order_by("id").first()


def can_access_client_dashboard(user, request=None) -> tuple[bool, object | None]:
    if not user or not user.is_authenticated:
        return False, None

    if getattr(user, "is_superuser", False):
        client = _resolve_superuser_client(request=request)
        return (client is not None), client

    client = get_user_client(user)
    if client is None:
        from apps.sites.models import Site

        site = Site.objects.select_related("owner").filter(owner=user, is_active=True).order_by("id").first()
        if site is not None:
            client, _ = get_or_create_client_for_site(site)

    if client is None:
        return False, None
    if not getattr(client, "is_active", False):
        return False, client
    return True, client


def has_active_subscription(client) -> bool:
    if client is None:
        return False
    if not billing_is_enabled():
        return True

    if Subscription.objects.filter(client=client, admin_override=True).exists():
        return True

    subscription = Subscription.objects.filter(
        client=client,
        status=Subscription.Status.ACTIVE,
        paid_until__gt=timezone.now(),
    ).first()
    return bool(subscription)


def resolve_plan_code(plan) -> str | None:
    if plan is None:
        return None

    slug = str(getattr(plan, "slug", "") or "").strip().lower().replace("_", "-")
    name = " ".join(str(getattr(plan, "name", "") or "").strip().lower().split())
    if slug == "content-hosting" or slug.startswith("content-hosting-") or name in {
        "контент и хостинг",
        "контент + хостинг",
    }:
        return PLAN_CONTENT_HOSTING
    if slug == "business-analytics" or slug.startswith("business-analytics-") or name in {
        "бизнес-аналитика",
        "бизнес аналитика",
    }:
        return PLAN_BUSINESS_ANALYTICS

    # Неизвестный тариф нельзя повышать до полного доступа по умолчанию.
    return None


def _restore_plan_from_successful_payment(subscription):
    """Восстанавливает потерянную связь только по подтверждённому платежу."""
    if subscription is None or subscription.plan_id:
        return getattr(subscription, "plan", None)

    payment_plan = (
        SubscriptionPayment.objects
        .select_related("plan")
        .filter(
            client_id=subscription.client_id,
            status=SubscriptionPayment.Status.SUCCEEDED,
            plan__isnull=False,
        )
        .order_by("-activated_at", "-created_at")
        .first()
    )
    if payment_plan is None:
        return None

    subscription.plan = payment_plan.plan
    subscription.save(update_fields=["plan", "updated_at"])
    return subscription.plan


def get_access_profile(user, request=None, client=None) -> dict:
    if request is not None and hasattr(request, "_tracknode_access_profile"):
        return request._tracknode_access_profile

    is_platform_admin = is_platform_owner(user)

    if client is None and user and user.is_authenticated:
        _, client = can_access_client_dashboard(user, request=request)

    subscription = None
    if client is not None:
        subscription = Subscription.objects.select_related("plan").filter(client=client).first()

    active = bool(
        subscription
        and (
            subscription.admin_override
            or (
                subscription.status == Subscription.Status.ACTIVE
                and subscription.paid_until
                and subscription.paid_until > timezone.now()
            )
        )
    )
    plan = _restore_plan_from_successful_payment(subscription)
    entitlement_active = bool(active or (subscription and not billing_is_enabled()))
    plan_code = resolve_plan_code(plan)

    if is_platform_admin:
        allowed_features = BUSINESS_ANALYTICS_FEATURES
        plan_code = plan_code or PLAN_BUSINESS_ANALYTICS
        plan_title = getattr(plan, "name", "") or "Полный доступ"
    elif entitlement_active and plan_code == PLAN_CONTENT_HOSTING:
        allowed_features = CONTENT_HOSTING_FEATURES
        plan_title = getattr(plan, "name", "") or "Контент и хостинг"
    elif entitlement_active and plan_code == PLAN_BUSINESS_ANALYTICS:
        allowed_features = BUSINESS_ANALYTICS_FEATURES
        plan_title = getattr(plan, "name", "") or "Бизнес-аналитика"
    else:
        allowed_features = BASE_FEATURES
        plan_title = getattr(plan, "name", "") if plan_code else "Тариф не выбран"

    profile = {
        "plan": plan_code,
        "plan_title": plan_title,
        "allowed_features": list(allowed_features),
        "has_active_subscription": active,
    }
    if request is not None:
        request._tracknode_access_profile = profile
    return profile


def user_has_feature(user, feature: str, request=None, client=None) -> bool:
    return feature in get_access_profile(user, request=request, client=client)["allowed_features"]
