import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DownloadJob(models.Model):
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('DOWNLOADING', 'Downloading'),
        ('PROCESSING', 'Processing'),
        ('READY', 'Ready for Download'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_jobs')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, default='movie')
    title = models.CharField(max_length=255)
    release_year = models.CharField(max_length=10, blank=True, default='')
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
    quality = models.CharField(max_length=20, default='1080p')
    format = models.CharField(max_length=10, default='mp4')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    progress = models.FloatField(default=0.0)
    source_provider = models.CharField(max_length=50, default='AutoEmbed Direct')
    temporary_path = models.CharField(max_length=500, blank=True, default='')
    filename = models.CharField(max_length=255, blank=True, default='')
    file_size = models.BigIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'downloads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename or self.title} [{self.status}]"
