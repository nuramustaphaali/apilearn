from rest_framework import permissions

class IsCourseOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the course.
        return obj.instructor == request.user

from .models import Enrollment

class IsEnrolledOrInstructor(permissions.BasePermission):
    """
    Allows access only if the user is enrolled OR is the instructor.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Instructors can always access their own content
        # Check if obj is Course, Lesson, or Quiz and trace back to instructor
        if hasattr(obj, 'instructor'):
            if obj.instructor == request.user: return True
        elif hasattr(obj, 'course'):
            if obj.course.instructor == request.user: return True
        elif hasattr(obj, 'lesson'):
             if obj.lesson.course.instructor == request.user: return True

        # 2. Students must be enrolled
        # We need to find the Course object depending on what view we are in
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'lesson'):
            course = obj.lesson.course
        else:
            course = obj # It is the course itself

        return Enrollment.objects.filter(student=request.user, course=course).exists()

