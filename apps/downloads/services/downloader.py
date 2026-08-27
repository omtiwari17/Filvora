"""
Download execution service.

Handles the actual file download from an authorized provider source
into the job's temporary source directory.
"""
import os
import logging
import subprocess
import requests
from apps.downloads.services.storage import create_job_directory

logger = logging.getLogger(__name__)


def download_source(job_id: str, source_info: dict, filename: str) -> dict:
    """
    Download media from an authorized provider source.

    Args:
        job_id: The DownloadJob UUID string.
        source_info: Dict from provider.get_downloadable_source() with 'url', 'headers', etc.
        filename: The target filename for the downloaded source.

    Returns:
        dict with 'success', 'filepath', 'file_size', 'error'.
    """
    url = source_info.get('url', '')
    headers = source_info.get('headers', {})

    if not url:
        return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'No download URL provided.'}

    paths = create_job_directory(job_id)
    source_filepath = os.path.join(paths['source'], filename)

    try:
        # Attempt download via curl.exe first (Windows Schannel, avoids SSL revocation issues)
        success = _download_with_curl(url, source_filepath, headers)

        if not success:
            # Fallback to requests
            success = _download_with_requests(url, source_filepath, headers)

        if success and os.path.exists(source_filepath):
            file_size = os.path.getsize(source_filepath)
            if file_size > 0:
                logger.info(f"Downloaded source for job {job_id}: {file_size} bytes")
                return {'success': True, 'filepath': source_filepath, 'file_size': file_size, 'error': ''}
            else:
                return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'Downloaded file is empty (0 bytes).'}
        else:
            return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'Download failed — no file produced.'}

    except Exception as e:
        logger.error(f"Download failed for job {job_id}: {e}")
        return {'success': False, 'filepath': '', 'file_size': 0, 'error': str(e)}


def _download_with_curl(url: str, filepath: str, headers: dict) -> bool:
    """
    Download a file using curl.exe (Windows Schannel).

    Returns:
        True if download succeeded.
    """
    try:
        cmd = ['curl.exe', '-L', '-o', filepath, '--ssl-no-revoke', '-s', '--max-time', '3600']
        for key, value in headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        return result.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.warning(f"curl download failed: {e}")
        return False


def _download_with_requests(url: str, filepath: str, headers: dict) -> bool:
    """
    Download a file using the requests library with streaming.

    Returns:
        True if download succeeded.
    """
    try:
        with requests.get(url, headers=headers, stream=True, timeout=3600) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
        return os.path.exists(filepath) and os.path.getsize(filepath) > 0
    except Exception as e:
        logger.warning(f"requests download failed: {e}")
        return False
