from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from djoser.views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import register, activate_account, dashboard, student_dashboard, instructor_dashboard
from django.contrib.auth.views import LoginView, LogoutView
from courses.views import CourseListView, CourseViewSet, CategoryViewSet, LessonViewSet, QuizViewSet, EnrollmentViewSet

# API Router
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='api-course')
router.register(r'categories', CategoryViewSet, basename='api-category')
router.register(r'lessons', LessonViewSet, basename='api-lesson')
router.register(r'quizzes', QuizViewSet, basename='api-quiz')
router.register(r'enrollments', EnrollmentViewSet, basename='api-enrollment')

urlpatterns = [
    path('admin/', admin.site.urls),

    # ==============================
    # 🌍 HTML FRONTEND (THE WEBSITE)
    # ==============================
    path('', CourseListView.as_view(), name='course-list'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/student/', student_dashboard, name='student-dashboard'),
    path('dashboard/instructor/', instructor_dashboard, name='instructor-dashboard'),

    # Auth Pages
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate'),

    # App URLs
    path('courses/', include('courses.urls')),     
    path('communications/', include('communications.urls')),
    path('payments/', include('payments.urls')),

    # ==============================
    # 🤖 API V1
    # ==============================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/register/', UserViewSet.as_view({'post': 'create'}), name='api_register'),
    path('api/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)