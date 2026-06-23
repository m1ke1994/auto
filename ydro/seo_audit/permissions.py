from rest_framework import permissions

from apps.sites.models import Site
from clients.models import Client
from subscriptions.access import can_access_client_dashboard, has_active_subscription
from subscriptions.exceptions import PaymentRequired


class SEOAuditAccessPermission(permissions.BasePermission):
    message = (
        "\u0421\u0415\u041e-\u0430\u0443\u0434\u0438\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d "
        "\u0442\u043e\u043b\u044c\u043a\u043e \u0432\u043b\u0430\u0434\u0435\u043b\u044c\u0446\u0443 "
        "\u0432\u044b\u0431\u0440\u0430\u043d\u043d\u043e\u0433\u043e \u0441\u0430\u0439\u0442\u0430 "
        "\u0438\u043b\u0438 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443 "
        "\u043f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u044b."
    )

    def _request_value(self, request, key):
        value = request.query_params.get(key)
        if value not in (None, ""):
            return value

        try:
            data = request.data
        except Exception:
            data = {}
        if isinstance(data, dict):
            value = data.get(key)
            if value not in (None, ""):
                return value

        return request.headers.get(f"X-{key.replace('_', '-').title()}")

    def _safe_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _platform_admin(self, user) -> bool:
        return bool(getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))

    def _first_active_client(self):
        return Client.objects.filter(is_active=True).order_by("id").first()

    def _bind_site_context(self, request, site_id: int) -> bool:
        user = request.user
        site = Site.objects.select_related("owner").filter(id=site_id, is_active=True).first()
        if site is None:
            return False

        is_platform_admin = self._platform_admin(user)
        if not is_platform_admin and site.owner_id != user.id:
            return False

        client = getattr(site.owner, "client", None)
        if client is None:
            return False

        if not is_platform_admin and not getattr(client, "is_active", False):
            return False

        request.site = site
        request.seo_site = site
        request.client = client
        request.seo_platform_admin = is_platform_admin
        return True

    def _bind_client_context(self, request) -> bool:
        user = request.user
        is_platform_admin = self._platform_admin(user)

        has_access, client = can_access_client_dashboard(user, request=request)
        if not has_access and is_platform_admin:
            client = self._first_active_client()
            has_access = client is not None

        if not has_access or client is None:
            return False

        request.client = client
        request.seo_platform_admin = is_platform_admin
        return True

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        site_id = self._safe_int(
            self._request_value(request, "site_id")
            or self._request_value(request, "site")
            or self._request_value(request, "selected_site_id")
        )

        if site_id:
            has_access = self._bind_site_context(request, site_id)
        else:
            has_access = self._bind_client_context(request)

        if not has_access:
            return False

        if getattr(request, "seo_platform_admin", False):
            return True

        if has_active_subscription(getattr(request, "client", None)):
            return True

        raise PaymentRequired()
