from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )
    
    # We use email as the primary login identifier
    email = models.EmailField(_('email address'), unique=True)
    
    # New Fields
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # Fix for using email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name'] 

    def __str__(self):
        return self.email

# Signal to auto-create Profile (Keep this if you have other profile fields like avatar)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    # Copy full_name here automatically if needed, or just rely on User.full_name
    
    def __str__(self):
        return f"Profile of {self.user.username}"