from django.db import models
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

class LibraryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='library_items', null=True, blank=True)
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'library'
        constraints = [
            models.UniqueConstraint(fields=['user', 'profile', 'tmdb_id', 'media_type'], name='unique_user_profile_library_item')
        ]
        indexes = [
            models.Index(fields=['user', '-added_at']),
            models.Index(fields=['profile', '-added_at']),
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
        return f"{self.user.username}{prof_name} - {self.media_type} - {self.tmdb_id}"


class CustomCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_collections')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='custom_collections', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'library'
        ordering = ['-created_at']

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
        return f"{self.user.username}{prof_name} - {self.name}"


class CustomCollectionItem(models.Model):
    collection = models.ForeignKey(CustomCollection, on_delete=models.CASCADE, related_name='items')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, default='movie')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'library'
        constraints = [
            models.UniqueConstraint(fields=['collection', 'tmdb_id', 'media_type'], name='unique_collection_media_item')
        ]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.collection.name} -> {self.media_type}:{self.tmdb_id}"
