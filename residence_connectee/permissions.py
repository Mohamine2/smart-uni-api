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
    - Level 1 (Beginner, 0-2 XP): List & Retrieve (GET)
    - Level 2 (Intermediate, 3+ XP): Create (POST), Delete (DELETE), Rename (PUT/PATCH 'name')
    - Level 3 (Advanced, 5+ XP): Control states (PUT/PATCH 'is_on', 'power_consumption')
    - Level 4 (Expert, 7+ XP): View statistics custom action
    """
    message = "Your student level is too low to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_level = getattr(request.user, 'level', 1)

        # Expert : Smart Grid Statistics
        if view.action == 'statistics':
            if user_level < 4:
                self.message = "Expert level (7+ XP) required to view Smart Grid analytics."
                return False
            return True

        # Beginner : Default Read Only rights on GET methods
        if request.method in SAFE_METHODS:
            return True

        # Intermediate : Can create new devices
        if view.action == 'create':
            if user_level < 2:
                self.message = "Intermediate level (3+ XP) required to add appliances."
                return False
            return True

        # For actions on a specific object, global access at level 2 or higher is permitted
        # Fine-grained field filtering will be handled in has_object_permission
        if view.action in ['update', 'partial_update', 'destroy']:
            return user_level >= 2
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user_level = getattr(request.user, 'level', 1)

        # Intermediate : Can delete
        if request.method == 'DELETE':
            return user_level >= 2

        if request.method in ['PUT', 'PATCH']:
            advanced_fields = {'is_on', 'power_consumption'}
            requested_fields = set(request.data.keys())

            # Advanced: If the request attempts to modify an electrical state
            if advanced_fields.intersection(requested_fields):
                if user_level < 3:
                    self.message = "Advanced level (5+ XP) required to control granular states."
                    return False
                return True

            # Intermediate: Allowed if it modifies other fields (such as the device name)
            return user_level >= 2

        return False