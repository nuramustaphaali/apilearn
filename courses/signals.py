from django.db.models.signals import pre_save, post_save  # <--- Added post_save here
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, Enrollment

# --- Signal 1: Course Published Notification (Uses pre_save) ---
@receiver(pre_save, sender=Course)
def course_publish_notification(sender, instance, **kwargs):
    if instance.pk: # If updating an existing course
        try:
            old_course = Course.objects.get(pk=instance.pk)
            # Check if it was unpublished AND is now being published
            if not old_course.is_published and instance.is_published:
                send_mail(
                    subject=f"Course Published: {instance.title}",
                    message=f"Congratulations! Your course '{instance.title}' is now live on ApiLearn.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.instructor.email],
                    fail_silently=False,
                )
                print(f"📧 EMAIL SENT: Course Published - {instance.title}")
        except Course.DoesNotExist:
            pass

# --- Signal 2: Enrollment Welcome Email (Uses post_save) ---
@receiver(post_save, sender=Enrollment)
def send_enrollment_email(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject=f"Enrollment Confirmed: {instance.course.title}",
            message=f"Hi {instance.student.username},\n\nYou have successfully enrolled in {instance.course.title}.\nHappy Learning!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.student.email],
            fail_silently=False,
        )
        print(f"📧 EMAIL SENT: Enrollment for {instance.student.email}")

from .models import LessonProgress

@receiver(post_save, sender=LessonProgress)
def check_course_completion(sender, instance, **kwargs):
    if instance.is_completed:
        # Get all lessons in this course
        course = instance.lesson.course
        total_lessons = course.lessons.count()
        
        # Count how many this student has finished
        completed_count = LessonProgress.objects.filter(
            student=instance.student, 
            lesson__course=course, 
            is_completed=True
        ).count()

        # If 100% complete
        if total_lessons > 0 and completed_count == total_lessons:
            send_mail(
                subject=f"🎉 Course Completed: {course.title}",
                message=f"Congratulations {instance.student.username}!\n\nYou have finished all lessons in '{course.title}'.\nGreat job!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.student.email],
                fail_silently=True,
            )
            print(f"📧 EMAIL SENT: Course Completion for {instance.student.email}")
from .models import LessonProgress, Certificate
from .utils import generate_certificate_pdf 

@receiver(post_save, sender=LessonProgress)
def check_course_completion(sender, instance, **kwargs):
    if instance.is_completed:
        course = instance.lesson.course
        user = instance.student
        
        # Check logic: Are all lessons done?
        total_lessons = course.lessons.count()
        completed_count = LessonProgress.objects.filter(
            student=user, lesson__course=course, is_completed=True
        ).count()

        if total_lessons > 0 and completed_count == total_lessons:
            # 1. Create Certificate
            cert, created = Certificate.objects.get_or_create(student=user, course=course)

            # 2. Generate PDF (if new or missing)
            if created or not cert.pdf_file:
                pdf_path = generate_certificate_pdf(cert)
                cert.pdf_file = pdf_path
                cert.save()

                # 3. Send Email
                download_link = f"http://127.0.0.1:8000/certificate/{cert.id}/download/"
                send_mail(
                    subject=f"🏆 You earned a certificate for {course.title}!",
                    message=f"Well done, {user.username}!\n\nYour official certificate is ready.\nDownload here: {download_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
