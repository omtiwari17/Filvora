from django.db import models
from django.contrib.auth.models import User

class WatchProgress(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('movie', 'Movie'),
        ('tv', 'TV Series'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_progress')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='movie')
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
    position_seconds = models.FloatField(default=0.0)
    duration_seconds = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'watch'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tmdb_id', 'media_type', 'season', 'episode'],
                name='unique_user_content_watch_progress'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.media_type}:{self.tmdb_id} ({self.progress_percentage}%)"

    @property
    def progress_percentage(self):
        if self.duration_seconds > 0:
            pct = (self.position_seconds / self.duration_seconds) * 100
            return min(100, max(0, round(pct, 1)))
        return 0.0
