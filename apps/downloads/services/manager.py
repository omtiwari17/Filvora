"""
Download Manager — coordinates the complete download lifecycle.

Orchestrates:
1. Job creation with metadata from TMDB
2. Provider resolution
3. Disk space checks
4. Background worker dispatch
5. Job state transitions (QUEUED → DOWNLOADING → PROCESSING → READY / FAILED)
6. Retry logic
"""
import os
import time
import threading
import logging
from django.utils import timezone
from apps.downloads.models import DownloadJob
from apps.downloads.services.filename import generate_video_filename
from apps.downloads.services import storage, downloader, processor, validator, cleanup
from apps.downloads.providers import registry
from apps.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)

# Maximum concurrent download threads
MAX_CONCURRENT_DOWNLOADS = 2
_active_threads_lock = threading.Lock()
_active_threads: dict = {}


class DownloadManager:
    @staticmethod
    def get_temp_directory() -> str:
        """Return the root temporary download directory."""
        return storage.get_temp_root()

    @classmethod
    def create_job(cls, user, tmdb_id: int, media_type: str = 'movie',
                   season: int = None, episode: int = None, quality: str = '1080p') -> DownloadJob:
        """
        Create a new DownloadJob and dispatch background processing.

        Fetches title/year from TMDB, generates the deterministic filename,
        and starts the background worker thread.
        """
        client = TMDBClient()
        if media_type == 'movie':
            details = client.get_movie(tmdb_id)
            title = details.get('title', f"Movie {tmdb_id}")
            year = (details.get('release_date') or '')[:4]
        else:
            details = client.get_tv(tmdb_id)
            title = details.get('name', f"Series {tmdb_id}")
            year = (details.get('first_air_date') or '')[:4]

        filename = generate_video_filename(
            media_type=media_type,
            title=title,
            year=year,
            season=season,
            episode=episode,
            quality=quality,
            ext='mp4'
        )

        # Determine source provider
        provider = registry.find_provider(tmdb_id, media_type, season, episode)
        provider_name = provider.name if provider else 'Direct'

        job = DownloadJob.objects.create(
            user=user,
            tmdb_id=tmdb_id,
            media_type=media_type,
            title=title,
            release_year=year,
            season=season,
            episode=episode,
            quality=quality,
            filename=filename,
            source_provider=provider_name,
            status='QUEUED',
            progress=0.0
        )

        # Dispatch background worker
        cls._dispatch_worker(job.id)
        return job

    @classmethod
    def retry_job(cls, job_id) -> DownloadJob | None:
        """
        Retry a failed or cancelled job.

        Cleans up old temp data and requeues the job.
        """
        try:
            job = DownloadJob.objects.get(id=job_id)
        except DownloadJob.DoesNotExist:
            return None

        if job.status not in ('FAILED', 'CANCELLED'):
            return job

        # Clean up old temp data
        cleanup.cleanup_job(str(job.id))

        # Reset job state
        job.status = 'QUEUED'
        job.progress = 0.0
        job.error_message = ''
        job.temporary_path = ''
        job.file_size = 0
        job.started_at = None
        job.completed_at = None
        job.save()

        # Re-dispatch
        cls._dispatch_worker(job.id)
        return job

    @classmethod
    def _dispatch_worker(cls, job_id):
        """Start a background thread for download processing."""
        thread = threading.Thread(target=cls._process_job, args=(job_id,), daemon=True)
        with _active_threads_lock:
            _active_threads[str(job_id)] = thread
        thread.start()

    @classmethod
    def _process_job(cls, job_id):
        """
        Full download pipeline executed in a background thread.

        Pipeline stages:
        1. Provider resolution & pre-flight space check
        2. Real stream extraction / download with live byte progress
        3. FFmpeg remuxing / container processing
        4. Output validation
        5. Finalization to READY state
        """
        try:
            job = DownloadJob.objects.get(id=job_id)

            # --- Stage 1: DOWNLOADING ---
            job.status = 'DOWNLOADING'
            job.started_at = timezone.now()
            job.progress = 5.0
            job.save(update_fields=['status', 'started_at', 'progress'])

            # Resolve provider
            provider = registry.find_provider(
                job.tmdb_id, job.media_type, job.season, job.episode
            )

            source_info = {}
            if provider:
                source_info = provider.get_downloadable_source(
                    job.tmdb_id, job.media_type, job.season, job.episode, job.quality
                )

            # Pre-flight disk space check
            estimated_size = source_info.get('estimated_size', 1024 * 1024 * 50)
            space_check = storage.check_disk_space(estimated_size)
            if not space_check['sufficient']:
                cls._fail_job(job, space_check['message'])
                return

            def on_download_progress(percent, bytes_downloaded):
                try:
                    curr_job = DownloadJob.objects.get(id=job_id)
                    if curr_job.status == 'DOWNLOADING':
                        curr_job.progress = min(90.0, max(5.0, percent))
                        curr_job.file_size = bytes_downloaded
                        curr_job.save(update_fields=['progress', 'file_size'])
                except Exception:
                    pass

            # Download actual source stream
            dl_result = downloader.download_source(
                str(job.id), source_info, job.filename, progress_callback=on_download_progress
            )

            if not dl_result['success']:
                cls._fail_job(job, dl_result['error'])
                return

            source_filepath = dl_result['filepath']

            # --- Stage 2: PROCESSING ---
            job.refresh_from_db()
            if job.status == 'CANCELLED':
                cleanup.cleanup_job(str(job.id))
                return

            job.status = 'PROCESSING'
            job.progress = 92.0
            job.save(update_fields=['status', 'progress'])

            output_filepath = storage.get_output_filepath(str(job.id), job.filename)

            # Process through FFmpeg (or container remux/copy)
            proc_result = processor.process_media(source_filepath, output_filepath)

            if not proc_result['success']:
                cls._fail_job(job, f"Processing failed: {proc_result['error']}")
                return

            job.progress = 98.0
            job.save(update_fields=['progress'])

            # --- Stage 3: VALIDATION ---
            val_result = validator.validate_output(output_filepath)

            if not val_result['valid']:
                cls._fail_job(job, f"Validation failed: {val_result['error']}")
                return

            # --- Stage 4: READY ---
            job.temporary_path = output_filepath
            job.file_size = val_result['file_size']
            job.status = 'READY'
            job.progress = 100.0
            job.completed_at = timezone.now()
            job.save()

            logger.info(f"Download job {job.id} completed: {job.filename} ({storage.format_file_size(job.file_size)})")

        except Exception as e:
            logger.error(f"Download job {job_id} failed with exception: {e}")
            try:
                job = DownloadJob.objects.get(id=job_id)
                cls._fail_job(job, str(e))
            except Exception:
                pass
        finally:
            with _active_threads_lock:
                _active_threads.pop(str(job_id), None)

    @staticmethod
    def _fail_job(job: DownloadJob, error_message: str):
        """Mark a job as failed with an error message."""
        job.status = 'FAILED'
        job.error_message = error_message
        job.completed_at = timezone.now()
        job.save()
        logger.error(f"Download job {job.id} failed: {error_message}")

    @staticmethod
    def get_active_count(user=None) -> int:
        """Get the number of active (non-terminal) jobs."""
        qs = DownloadJob.objects.filter(status__in=['QUEUED', 'DOWNLOADING', 'PROCESSING'])
        if user:
            qs = qs.filter(user=user)
        return qs.count()
