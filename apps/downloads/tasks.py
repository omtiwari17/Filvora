"""
Background task orchestration for download jobs.

Provides a thread-based worker interface that mirrors the Celery task API.
When Redis/Celery are introduced, these functions become direct Celery tasks
with minimal refactoring.
"""
import logging
from apps.downloads.services.manager import DownloadManager
from apps.downloads.services.cleanup import cleanup_orphans, cleanup_completed_jobs

logger = logging.getLogger(__name__)


def process_download_job(job_id):
    """
    Process a download job in the background.

    This is the primary entry point for background processing.
    Currently dispatched via threading; designed for future Celery migration:

        @celery_app.task
        def process_download_job(job_id):
            DownloadManager._process_job(job_id)
    """
    DownloadManager._process_job(job_id)


def run_cleanup():
    """
    Run cleanup tasks:
    1. Remove orphaned job directories (crashes, power loss)
    2. Clean up temp data for completed jobs older than 48 hours
    """
    orphan_result = cleanup_orphans()
    logger.info(f"Orphan cleanup: {orphan_result['removed']} removed, {len(orphan_result['errors'])} errors")

    completed_cleaned = cleanup_completed_jobs(max_age_hours=48)
    logger.info(f"Completed job cleanup: {completed_cleaned} directories cleaned")

    return {
        'orphans_removed': orphan_result['removed'],
        'completed_cleaned': completed_cleaned,
        'errors': orphan_result['errors']
    }
