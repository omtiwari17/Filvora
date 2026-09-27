from django.contrib import admin
from .models import WatchProgress, UserRating


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'profile',
        'tmdb_id',
        'media_type',
        'season_episode_display',
        'progress_percentage',
        'completed',
        'watch_date_display',
        'updated_at'
    )
    list_filter = ('media_type', 'completed', 'created_at', 'updated_at')
    search_fields = ('user__username', 'profile__name', 'tmdb_id')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at', 'progress_percentage')

    def season_episode_display(self, obj):
        if obj.media_type == 'tv' and obj.season is not None:
            return f"S{obj.season:02d}E{obj.episode or 1:02d}"
        return "—"
    season_episode_display.short_description = 'Episode'


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'tmdb_id', 'media_type', 'score_stars', 'updated_at')
    list_filter = ('media_type', 'score', 'updated_at')
    search_fields = ('user__username', 'profile__name', 'tmdb_id')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')

    def score_stars(self, obj):
        return f"{'★' * obj.score}{'☆' * (5 - obj.score)} ({obj.score}/5)"
    score_stars.short_description = 'Rating'
