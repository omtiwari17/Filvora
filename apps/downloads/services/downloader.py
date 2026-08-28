"""
Download execution service.

Handles actual media stream extraction and downloading from authorized provider sources
into the job's temporary source directory.
Supports yt-dlp for high-definition video extraction with real-time byte progress hooks,
plus curl/requests fallbacks for direct MP4 URLs.
"""
import os
import logging
import subprocess
import requests
from apps.downloads.services.storage import create_job_directory

logger = logging.getLogger(__name__)


def download_source(job_id: str, source_info: dict, filename: str, progress_callback=None) -> dict:
    """
    Download media from an authorized provider source.

    Args:
        job_id: The DownloadJob UUID string.
        source_info: Dict from provider.get_downloadable_source() with 'url', 'headers', etc.
        filename: The target filename for the downloaded source.
        progress_callback: Optional callable(percent: float, downloaded_bytes: int)

    Returns:
        dict with 'success', 'filepath', 'file_size', 'error'.
    """
    url = source_info.get('url', '')
    headers = source_info.get('headers', {})
    quality = source_info.get('quality', '1080p')

    if not url:
        return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'No download stream URL available for this title.'}

    paths = create_job_directory(job_id)
    source_filepath = os.path.join(paths['source'], filename)

    try:
        # If URL is a stream or video portal URL (YouTube, Vimeo, HLS, etc.), use yt-dlp
        if 'youtube.com' in url or 'youtu.be' in url or 'vimeo.com' in url or url.endswith('.m3u8') or url.endswith('.mpd'):
            success = _download_with_ytdlp(url, source_filepath, quality, progress_callback)
            if success and os.path.exists(source_filepath):
                file_size = os.path.getsize(source_filepath)
                if file_size > 0:
                    logger.info(f"yt-dlp downloaded stream for job {job_id}: {file_size} bytes")
                    return {'success': True, 'filepath': source_filepath, 'file_size': file_size, 'error': ''}

        # Fallback to direct curl.exe (Windows Schannel)
        success = _download_with_curl(url, source_filepath, headers)

        if not success:
            # Fallback to requests
            success = _download_with_requests(url, source_filepath, headers, progress_callback)

        if success and os.path.exists(source_filepath):
            file_size = os.path.getsize(source_filepath)
            if file_size > 0:
                logger.info(f"Downloaded source for job {job_id}: {file_size} bytes")
                return {'success': True, 'filepath': source_filepath, 'file_size': file_size, 'error': ''}
            else:
                return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'Downloaded file is empty (0 bytes).'}
        else:
            return {'success': False, 'filepath': '', 'file_size': 0, 'error': 'Download failed — stream could not be retrieved.'}

    except Exception as e:
        logger.error(f"Download failed for job {job_id}: {e}")
        return {'success': False, 'filepath': '', 'file_size': 0, 'error': str(e)}


def _download_with_ytdlp(url: str, output_filepath: str, quality: str, progress_callback=None) -> bool:
    """Download video stream using yt-dlp python library with progress reporting."""
    try:
        import yt_dlp

        height_limit = 1080
        if '720' in quality:
            height_limit = 720
        elif '480' in quality:
            height_limit = 480

        def ytdl_hook(d):
            if d.get('status') == 'downloading' and progress_callback:
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = min(90.0, (downloaded / total) * 90.0)
                    progress_callback(percent, downloaded)

        # Output template base without extension (yt-dlp adds extension or merges to mp4)
        base_path, _ = os.path.splitext(output_filepath)
        outtmpl = f"{base_path}.%(ext)s"

        ydl_opts = {
            'format': f'bestvideo[height<={height_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height_limit}][ext=mp4]/best',
            'outtmpl': outtmpl,
            'merge_output_format': 'mp4',
            'progress_hooks': [ytdl_hook],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # If downloaded file has a slightly different extension, rename/ensure it matches output_filepath
        if os.path.exists(output_filepath) and os.path.getsize(output_filepath) > 0:
            return True

        # Check for possible merged .mp4
        mp4_path = f"{base_path}.mp4"
        if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
            if mp4_path != output_filepath:
                os.replace(mp4_path, output_filepath)
            return True

        return False

    except Exception as e:
        logger.warning(f"yt-dlp download failed: {e}")
        return False


def _download_with_curl(url: str, filepath: str, headers: dict) -> bool:
    """Download a file using curl.exe (Windows Schannel)."""
    try:
        cmd = ['curl.exe', '-L', '-o', filepath, '--ssl-no-revoke', '-s', '--connect-timeout', '15', '--max-time', '600']
        for key, value in headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, timeout=610)
        return result.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.warning(f"curl download failed: {e}")
        return False


def _download_with_requests(url: str, filepath: str, headers: dict, progress_callback=None) -> bool:
    """Download a file using requests library with streaming."""
    try:
        with requests.get(url, headers=headers, stream=True, timeout=(10, 600)) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):  # 512KB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            percent = min(90.0, (downloaded / total_size) * 90.0)
                            progress_callback(percent, downloaded)

        return os.path.exists(filepath) and os.path.getsize(filepath) > 0
    except Exception as e:
        logger.warning(f"requests download failed: {e}")
        return False
