"""
Temporary storage management for download jobs.

Handles:
- Per-job temp directory creation (media/downloads/temp/job_<id>/{source,processing,output})
- Disk space estimation and pre-flight checks
- Cleanup of job directories after completion/failure/cancellation
"""
import os
import shutil
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_temp_root() -> str:
    """Return the root temporary download directory, creating it if needed."""
    temp_root = os.path.join(settings.BASE_DIR, 'media', 'downloads', 'temp')
    os.makedirs(temp_root, exist_ok=True)
    return temp_root


def create_job_directory(job_id: str) -> dict:
    """
    Create the per-job temporary directory structure.

    Returns:
        dict with 'root', 'source', 'processing', 'output' paths.
    """
    temp_root = get_temp_root()
    job_dir = os.path.join(temp_root, f'job_{job_id}')

    paths = {
        'root': job_dir,
        'source': os.path.join(job_dir, 'source'),
        'processing': os.path.join(job_dir, 'processing'),
        'output': os.path.join(job_dir, 'output'),
    }

    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    logger.info(f"Created job directory: {job_dir}")
    return paths


def cleanup_job_directory(job_id: str) -> bool:
    """
    Remove the entire job directory tree.

    Returns:
        True if cleanup succeeded, False otherwise.
    """
    temp_root = get_temp_root()
    job_dir = os.path.join(temp_root, f'job_{job_id}')

    if os.path.exists(job_dir):
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.info(f"Cleaned up job directory: {job_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up job directory {job_dir}: {e}")
            return False
    return True


def check_disk_space(required_bytes: int) -> dict:
    """
    Check whether sufficient disk space is available.

    Args:
        required_bytes: Estimated bytes needed (including temp processing overhead).

    Returns:
        dict with 'available_bytes', 'required_bytes', 'sufficient' (bool), 'message'.
    """
    temp_root = get_temp_root()

    try:
        disk_usage = shutil.disk_usage(temp_root)
        available = disk_usage.free
    except Exception:
        # If we can't determine disk space, allow the download to proceed
        return {
            'available_bytes': 0,
            'required_bytes': required_bytes,
            'sufficient': True,
            'message': 'Unable to determine available disk space.'
        }

    # Add 20% overhead for processing buffers
    total_required = int(required_bytes * 1.2) if required_bytes > 0 else 0

    sufficient = available >= total_required if total_required > 0 else True

    if not sufficient:
        available_gb = available / (1024 ** 3)
        required_gb = total_required / (1024 ** 3)
        message = f"Not enough disk space. Required: {required_gb:.1f} GB, Available: {available_gb:.1f} GB"
    else:
        message = 'Sufficient disk space available.'

    return {
        'available_bytes': available,
        'required_bytes': total_required,
        'sufficient': sufficient,
        'message': message
    }


def get_output_filepath(job_id: str, filename: str) -> str:
    """Return the full path for the final output file inside the job's output directory."""
    temp_root = get_temp_root()
    output_dir = os.path.join(temp_root, f'job_{job_id}', 'output')
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable file size string."""
    if size_bytes <= 0:
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f'{size:.1f} {units[i]}'
