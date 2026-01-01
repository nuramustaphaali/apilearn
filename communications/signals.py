from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Announcement, Notification
from courses.models import Enrollment

@receiver(post_save, sender=Announcement)
def broadcast_announcement(sender, instance, created, **kwargs):
    if created:
        # 1. Find all enrolled students
        enrollments = Enrollment.objects.filter(course=instance.course)
        
        # 2. Prepare Email List
        recipient_emails = []
        
        for enrollment in enrollments:
            student = enrollment.student
            
            # A. Create In-App Notification
            Notification.objects.create(
                user=student,
                message=f"New Announcement in {instance.course.title}: {instance.title}",
                link=f"/courses/{instance.course.id}/" # Link to course
            )
            
            # B. Add to email list
            recipient_emails.append(student.email)

        # 3. Send Mass Email (Bulk is better for performance)
        if recipient_emails:
            send_mail(
                subject=f"📢 {instance.course.title}: {instance.title}",
                message=f"{instance.content}\n\n- {instance.instructor.username}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[], # Leave empty to use bcc
                bcc=recipient_emails, # Use BCC to hide student emails from each other
                fail_silently=True,
            )
            print(f"📧 BROADCAST SENT: {len(recipient_emails)} students notified.")