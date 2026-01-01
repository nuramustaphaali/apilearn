from rest_framework import permissions

class IsInstructor(permissions.BasePermission):
    """
    Allows access only to instructors.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'instructor'

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsStudent(permissions.BasePermission):
    """
    Allows access only to students.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'