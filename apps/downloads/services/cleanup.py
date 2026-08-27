"""
Cleanup service for download temporary data.

Handles:
- Removal of temp files after job success/failure/cancellation
- Orphan directory cleanup after crashes or power loss
- Scheduled cleanup of abandoned directories
"""
import os
import time
import shutil
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Orphan directories older than this (in seconds) are considered abandoned
ORPHAN_MAX_AGE = 24 * 60 * 60  # 24 hours


def cleanup_job(job_id: str) -> bool:
    """
    Clean up all temporary data for a specific job.

    Args:
        job_id: The DownloadJob UUID string.

    Returns:
        True if cleanup succeeded.
    """
    from apps.downloads.services.storage import cleanup_job_directory
    return cleanup_job_directory(job_id)


def cleanup_orphans() -> dict:
    """
    Find and remove orphaned job directories that don't correspond
    to any active job, or that are older than ORPHAN_MAX_AGE.

    Returns:
        dict with 'removed' (count) and 'errors' (list).
    """
    from apps.downloads.models import DownloadJob

    temp_root = os.path.join(settings.BASE_DIR, 'media', 'downloads', 'temp')
    result = {'removed': 0, 'errors': []}

    if not os.path.exists(temp_root):
        return result

    # Get all active job IDs
    active_job_ids = set(
        str(jid) for jid in
        DownloadJob.objects.filter(
            status__in=['QUEUED', 'DOWNLOADING', 'PROCESSING']
        ).values_list('id', flat=True)
    )

    now = time.time()

    for entry in os.listdir(temp_root):
        entry_path = os.path.join(temp_root, entry)

        if not os.path.isdir(entry_path):
            continue

        if not entry.startswith('job_'):
            continue

        # Extract job ID from directory name
        job_id_str = entry[4:]  # Remove 'job_' prefix

        # Skip directories belonging to active jobs
        if job_id_str in active_job_ids:
            continue

        # Check age
        try:
            dir_mtime = os.path.getmtime(entry_path)
            age = now - dir_mtime

            if age > ORPHAN_MAX_AGE:
                shutil.rmtree(entry_path, ignore_errors=True)
                result['removed'] += 1
                logger.info(f"Removed orphan directory: {entry_path} (age: {age/3600:.1f}h)")
        except Exception as e:
            result['errors'].append(f"Failed to process {entry_path}: {e}")

    return result


def cleanup_completed_jobs(max_age_hours: int = 48) -> int:
    """
    Clean up temp directories for completed/failed/cancelled jobs
    older than max_age_hours.

    Returns:
        Number of directories cleaned up.
    """
    from apps.downloads.models import DownloadJob
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(hours=max_age_hours)

    old_jobs = DownloadJob.objects.filter(
        status__in=['READY', 'FAILED', 'CANCELLED'],
        completed_at__lt=cutoff
    )

    cleaned = 0
    for job in old_jobs:
        if cleanup_job(str(job.id)):
            if job.temporary_path:
                job.temporary_path = ''
                job.save(update_fields=['temporary_path'])
            cleaned += 1

    return cleaned
