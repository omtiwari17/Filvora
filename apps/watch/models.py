from django.db import models
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

class WatchProgress(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('movie', 'Movie'),
        ('tv', 'TV Series'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_progress')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='watch_progress', null=True, blank=True)
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
                fields=['user', 'profile', 'tmdb_id', 'media_type', 'season', 'episode'],
                name='unique_user_profile_content_watch_progress'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['profile', '-updated_at']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        prof_name = f" [{self.profile.name}]" if self.profile else ""
        return f"{self.user.username}{prof_name} - {self.media_type}:{self.tmdb_id} ({self.progress_percentage}%)"

    @property
    def progress_percentage(self):
        if self.duration_seconds > 0:
            pct = (self.position_seconds / self.duration_seconds) * 100
            return min(100, max(0, round(pct, 1)))
        return 0.0

    def save(self, *args, **kwargs):
        if not self.profile_id and self.user_id:
            first_p = UserProfile.objects.filter(user_id=self.user_id).first()
            if not first_p:
                first_p = UserProfile.objects.create(
                    user_id=self.user_id,
                    name=self.user.username.capitalize() if self.user else "User",
                    avatar=f"https://ui-avatars.com/api/?name={self.user.username if self.user else 'User'}&background=111827&color=fff&bold=true",
                    is_kids=False
                )
            self.profile = first_p
        super().save(*args, **kwargs)


class UserRating(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('movie', 'Movie'),
        ('tv', 'TV Series'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ratings', null=True, blank=True)
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='movie')
    score = models.IntegerField()  # 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'watch'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'profile', 'tmdb_id', 'media_type'],
                name='unique_user_profile_content_rating'
            )
        ]
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.profile_id and self.user_id:
            first_p = UserProfile.objects.filter(user_id=self.user_id).first()
            if not first_p:
                first_p = UserProfile.objects.create(
                    user_id=self.user_id,
                    name=self.user.username.capitalize() if self.user else "User",
                    avatar=f"https://ui-avatars.com/api/?name={self.user.username if self.user else 'User'}&background=111827&color=fff&bold=true",
                    is_kids=False
                )
            self.profile = first_p
        super().save(*args, **kwargs)

    def __str__(self):
        prof_name = f" [{self.profile.name}]" if self.profile else ""
        return f"{self.user.username}{prof_name} rated {self.media_type}:{self.tmdb_id} = {self.score}/5"

