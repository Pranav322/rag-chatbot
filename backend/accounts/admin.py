"""
Django Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for email-based User model."""
    
    list_display = ('email', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login')
