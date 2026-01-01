from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import register, activate_account
from users.views import edit_profile, dashboard, student_dashboard, instructor_dashboard


urlpatterns = [
    # HTML Views
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Helper
    path('profile/edit/', edit_profile, name='edit-profile'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/student/', student_dashboard, name='student-dashboard'),
    path('dashboard/instructor/', instructor_dashboard, name='instructor-dashboard'),
]