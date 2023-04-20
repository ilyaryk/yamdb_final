from rest_framework import permissions


class AuthorModeratorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            or (request.user.is_authenticated and request.user.is_moderator)
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or (request.user.is_authenticated and request.user.is_moderator)
        )


class IsAdmin(permissions.BasePermission):
    """Класс реализует права только для администраторов."""

    message = "Ошибка: Пользователь должен быть администратором."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

    def has_object_permission(self, request, view, obj):
        return request.user.is_admin
