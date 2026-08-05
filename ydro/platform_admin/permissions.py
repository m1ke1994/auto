from rest_framework.permissions import BasePermission


def is_platform_owner(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_staff", False)
            or user.has_perm("platform_admin.access_platform")
        )
    )


class IsPlatformOwner(BasePermission):
    message = "Доступ к управлению платформой запрещён."

    def has_permission(self, request, view):
        return is_platform_owner(request.user)


class CanViewPlatformPersonalData(BasePermission):
    message = "Нет разрешения на просмотр персональных данных."

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("platform_admin.view_platform_personal_data"))


class CanManagePlatformRecommendations(BasePermission):
    message = "Нет разрешения на управление рекомендациями."

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("platform_admin.manage_platform_recommendations"))

