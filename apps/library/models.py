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
