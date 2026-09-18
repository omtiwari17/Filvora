from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
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

    @property
    def effective_end_dt(self):
        """Returns the terminal timestamp of the watch session (completed_at or updated_at)."""
        if self.completed:
            return self.completed_at or self.updated_at
        return self.updated_at

    @property
    def effective_start_dt(self):
        """Returns the start timestamp, guaranteed not to exceed the terminal timestamp."""
        start = self.created_at or self.updated_at
        end = self.effective_end_dt
        if start and end and start > end:
            return end
        return start or end

    @property
    def is_multi_day(self):
        """Returns True if the watch session spanned across different calendar dates."""
        start_dt = self.effective_start_dt
        end_dt = self.effective_end_dt
        if not start_dt or not end_dt:
            return False
        return start_dt.date() != end_dt.date()

    @property
    def watch_date_display(self):
        """
        Human-friendly watch date representation:
        - If single day: 'Sep 18, 2026'
        - If multi-day: 'Sep 15 – 18, 2026' (chronologically ordered from earlier to later)
        """
        start_dt = self.effective_start_dt
        end_dt = self.effective_end_dt
        if not start_dt and not end_dt:
            return ""

        start_d = (start_dt or end_dt).date()
        end_d = (end_dt or start_dt).date()

        # Enforce chronological ordering
        if start_d > end_d:
            start_d, end_d = end_d, start_d

        if start_d == end_d:
            return end_d.strftime("%b %d, %Y")

        if start_d.year == end_d.year:
            if start_d.month == end_d.month:
                return f"{start_d.strftime('%b %d')} – {end_d.strftime('%d, %Y')}"
            return f"{start_d.strftime('%b %d')} – {end_d.strftime('%b %d, %Y')}"
        return f"{start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')}"

    @property
    def watch_date_tooltip(self):
        start_dt = self.effective_start_dt
        end_dt = self.effective_end_dt
        if not start_dt and not end_dt:
            return ""

        start_d = (start_dt or end_dt).date()
        end_d = (end_dt or start_dt).date()
        if start_d > end_d:
            start_dt, end_dt = end_dt, start_dt
            start_d, end_d = end_d, start_d

        start_str = start_dt.strftime("%b %d, %Y")
        end_str = end_dt.strftime("%b %d, %Y")

        if self.completed:
            if start_d == end_d:
                return f"Completed on {end_str}"
            return f"Started {start_str} • Completed {end_str}"
        else:
            if start_d == end_d:
                return f"Started on {start_str}"
            return f"Started {start_str} • Last played {end_str}"

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

