from django.contrib import admin
from .models import PlaybackServerPreference


@admin.register(PlaybackServerPreference)
class PlaybackServerPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'media_type', 'tmdb_id', 'season', 'episode', 'provider_id', 'last_successful_at')
    list_filter = ('provider_id', 'media_type', 'last_successful_at')
    search_fields = ('user__username', 'provider_id', 'tmdb_id')
    ordering = ('-last_successful_at',)
    readonly_fields = ('last_successful_at',)
