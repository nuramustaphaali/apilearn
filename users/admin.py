from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

# 1. Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    
    # What to see in the list of users
    list_display = ('email', 'username', 'full_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('email',)

    # Editing an existing user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'role')}), # Added full_name & role here
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Creating a NEW user in Admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'role', 'password', 'confirm_password'),
        }),
    )

# 2. Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role', 'avatar')
    search_fields = ('user__username', 'user__email')

    # Helper to show role in Profile list
    def get_role(self, obj):
        return obj.user.role
    get_role.short_description = 'Role'