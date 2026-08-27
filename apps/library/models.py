from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LibraryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'library'
        constraints = [
            models.UniqueConstraint(fields=['user', 'tmdb_id', 'media_type'], name='unique_library_item')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.media_type} - {self.tmdb_id}"


class CustomCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'library'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


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
