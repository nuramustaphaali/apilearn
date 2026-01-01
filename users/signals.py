from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import pre_save

@receiver(pre_save, sender=User)
def check_role_change(sender, instance, **kwargs):
    """
    Detects if the role is changing. If so, sends an email notification.
    """
    if instance.pk: # If user already exists (not a new creation)
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.role != instance.role:
                # Role has changed!
                send_mail(
                    subject="Role Update Notification",
                    message=f"Hello {instance.username},\n\nYour account role has been updated to: {instance.get_role_display()}.\n\nRegards,\nApiLearn Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
                print(f"📧 EMAIL SENT: Role changed for {instance.email} to {instance.role}")
        except User.DoesNotExist:
            pass