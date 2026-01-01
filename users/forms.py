from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'nice-select'}))

    class Meta:
        model = User
        fields = ['full_name', 'email', 'role'] # Password is added by UserCreationForm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email # Force username to be email
        if commit:
            user.save()
        return user

# users/forms.py
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255, required=True)
    
    class Meta:
        model = Profile
        fields = ['avatar', 'bio'] # We handle full_name manually in the view