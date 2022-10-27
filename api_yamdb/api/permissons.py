from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Ограничение прав доступа изменения контента только для админа,
    чтение — для любого пользователя.
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_admin
        )


class IsAdmin(BasePermission):
    """
    Ограничение прав доступа изменения контента только для админа.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff or request.user.is_admin


class IsAuthorOrModerator(BasePermission):
    """
    Ограничение прав доступа изменения контента только для автора
    и модератора.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.is_moderator
        )
