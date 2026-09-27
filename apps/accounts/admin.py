from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_kids', 'created_at')
    list_filter = ('is_kids', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
