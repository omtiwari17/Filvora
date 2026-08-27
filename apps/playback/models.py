from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PlaybackServerPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_preferences')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, default='movie')
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
    provider_id = models.CharField(max_length=50)
    last_successful_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'playback'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tmdb_id', 'media_type', 'season', 'episode'],
                name='unique_user_media_server_preference'
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.media_type}:{self.tmdb_id} ({self.provider_id})"
