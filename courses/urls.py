from django.urls import path
from .views import (
    CourseListView, CourseDetailView, 
    CourseCreateView, CourseUpdateView, CourseDeleteView,
    LessonCreateView, 
    toggle_lesson_completion, QuizCreateView, add_question, take_quiz, download_certificate, verify_certificate
)

urlpatterns = [
    # Public Views
    path('', CourseListView.as_view(), name='course-list'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    
    # Instructor Actions (The new stuff!)
    path('create/', CourseCreateView.as_view(), name='course-create'),
    path('<int:pk>/edit/', CourseUpdateView.as_view(), name='course-edit'),
    path('<int:pk>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    
    # Lesson Actions
    path('<int:course_id>/add-lesson/', LessonCreateView.as_view(), name='lesson-add'),
    path('lesson/<int:lesson_id>/toggle/', toggle_lesson_completion, name='lesson-toggle'),

    path('quiz/<int:pk>/take/', take_quiz, name='take-quiz'),

    # Certificates

    path('course/<int:course_id>/add-quiz/', QuizCreateView.as_view(), name='quiz-create'),
    path('quiz/<int:quiz_id>/add-question/', add_question, name='question-add'),

    path('certificate/<uuid:cert_id>/download/', download_certificate, name='download-cert'),
    path('certificate/verify/', verify_certificate, name='verify-cert'),
]