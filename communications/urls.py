from django.urls import path
from .views import NotificationListView, MarkNotificationRead, MarkAllRead, AnnouncementCreateView

urlpatterns = [
    path('inbox/', NotificationListView.as_view(), name='inbox'),
    path('read/<int:pk>/', MarkNotificationRead.as_view(), name='mark-read'),
    path('read/all/', MarkAllRead.as_view(), name='mark-all-read'),
    path('announce/<int:course_id>/', AnnouncementCreateView.as_view(), name='create-announcement'),
]