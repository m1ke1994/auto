from rest_framework.permissions import BasePermission


class IsPlatformOwner(BasePermission):
    message = "Доступ к управлению платформой запрещён."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.has_perm("platform_admin.access_platform"))


class CanViewPlatformPersonalData(BasePermission):
    message = "Нет разрешения на просмотр персональных данных."

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("platform_admin.view_platform_personal_data"))


class CanManagePlatformRecommendations(BasePermission):
    message = "Нет разрешения на управление рекомендациями."

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("platform_admin.manage_platform_recommendations"))

