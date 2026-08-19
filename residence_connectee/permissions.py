from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Read-only access for regular users; write operations restricted to staff.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class HasDeviceLevelPermission(BasePermission):
    """
    Role-based permission checking the student's gamification level:
    - Level >= 1 : Create (POST), List & Retrieve (GET)
    - Level >= 2 : Update / Configure (PUT/PATCH), Delete (DELETE)
    - Level >= 3 : View statistics custom action
    """
    message = "Your student level is too low to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_level = getattr(request.user, 'level', 1)

        if view.action == 'statistics':
            return user_level >= 3

        if view.action in ['update', 'partial_update', 'destroy']:
            return user_level >= 2

        return user_level >= 1