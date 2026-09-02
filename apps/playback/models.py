from django.db import models
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

class PlaybackServerPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_preferences')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='server_preferences', null=True, blank=True)
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
                fields=['user', 'profile', 'tmdb_id', 'media_type', 'season', 'episode'],
                name='unique_user_profile_media_server_preference'
            )
        ]

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
        return f"{self.user.username}{prof_name} -> {self.media_type}:{self.tmdb_id} ({self.provider_id})"
