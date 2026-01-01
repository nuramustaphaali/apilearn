from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, View
from django.urls import reverse
from .models import Notification, Announcement
from courses.models import Course

# --- NOTIFICATIONS (INBOX) ---
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'communications/inbox.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class MarkNotificationRead(LoginRequiredMixin, View):
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        
        # Redirect to the link if it exists, otherwise back to inbox
        if notification.link:
            return redirect(notification.link)
        return redirect('inbox')

class MarkAllRead(LoginRequiredMixin, View):
    def get(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect('inbox')

# --- ANNOUNCEMENTS (INSTRUCTOR) ---
class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Announcement
    template_name = 'communications/announcement_form.html'
    fields = ['title', 'content']

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('course-detail', kwargs={'pk': self.course.id})

    def test_func(self):
        # Only the instructor can post
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return self.request.user == course.instructor