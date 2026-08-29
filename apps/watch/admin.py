from django.contrib import admin
from .models import WatchProgress, UserRating

@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'media_type', 'season', 'episode', 'progress_percentage', 'completed', 'updated_at')
    list_filter = ('media_type', 'completed')
    search_fields = ('user__username', 'tmdb_id')

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'media_type', 'score', 'updated_at')
    list_filter = ('media_type', 'score')
    search_fields = ('user__username', 'tmdb_id')
