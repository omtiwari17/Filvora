from django.contrib import admin
from apps.downloads.models import DownloadJob


@admin.register(DownloadJob)
class DownloadJobAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'media_type', 'quality', 'status', 'progress', 'created_at', 'completed_at')
    list_filter = ('status', 'media_type', 'quality')
    search_fields = ('title', 'filename', 'user__username')
    readonly_fields = ('id', 'created_at', 'started_at', 'completed_at')
    ordering = ('-created_at',)
