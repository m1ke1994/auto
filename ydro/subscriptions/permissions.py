from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from subscriptions.access import (
    ACTIVE_PLAN_REQUIRED_MESSAGE,
    BUSINESS_ONLY_FEATURES,
    BUSINESS_ANALYTICS_REQUIRED_MESSAGE,
    get_access_profile,
    has_active_subscription,
)
from subscriptions.exceptions import PaymentRequired


class HasActiveSubscription(permissions.BasePermission):
    message = "Подписка не активна."

    def has_permission(self, request, view):
        client = getattr(request, "client", None)
        if client is None:
            return True

        if has_active_subscription(client):
            return True

        raise PaymentRequired()


class HasFeatureAccess(permissions.BasePermission):
    message = BUSINESS_ANALYTICS_REQUIRED_MESSAGE

    def has_permission(self, request, view):
        required_feature = getattr(view, "required_feature", None)
        if not required_feature:
            return True

        profile = get_access_profile(
            request.user,
            request=request,
            client=getattr(request, "client", None),
        )
        if required_feature in profile["allowed_features"]:
            return True

        detail = self.message if required_feature in BUSINESS_ONLY_FEATURES else ACTIVE_PLAN_REQUIRED_MESSAGE
        raise PermissionDenied(detail=detail)
