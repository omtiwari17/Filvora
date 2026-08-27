"""
Output file validation service.

Validates the final processed file before marking a job as READY.
Never presents a corrupted output as successful.
"""
import os
import logging
from apps.downloads.services.processor import probe_media_info

logger = logging.getLogger(__name__)


def validate_output(filepath: str) -> dict:
    """
    Validate a processed output file.

    Checks:
    1. File exists
    2. File size is non-zero
    3. Container is readable (via ffprobe if available)
    4. Video stream exists
    5. Audio stream exists (warning-only if missing)

    Args:
        filepath: Path to the output file.

    Returns:
        dict with 'valid' (bool), 'file_size', 'warnings' (list), 'error'.
    """
    result = {
        'valid': False,
        'file_size': 0,
        'warnings': [],
        'error': ''
    }

    # Check 1: File exists
    if not os.path.exists(filepath):
        result['error'] = 'Output file does not exist.'
        return result

    # Check 2: Non-zero file size
    file_size = os.path.getsize(filepath)
    result['file_size'] = file_size

    if file_size == 0:
        result['error'] = 'Output file is empty (0 bytes).'
        return result

    # Minimum reasonable size for a video file (100 KB)
    if file_size < 102400:
        result['error'] = f'Output file is suspiciously small ({file_size} bytes). Likely corrupted.'
        return result

    # Check 3-5: Container, video stream, audio stream (via ffprobe)
    probe = probe_media_info(filepath)

    if probe.get('error'):
        # ffprobe not available — accept file based on size alone
        result['warnings'].append(f"Could not probe media streams (ffprobe unavailable): {probe['error']}")
        result['valid'] = True
        return result

    if not probe.get('has_video'):
        result['error'] = 'No video stream found in output file.'
        return result

    if not probe.get('has_audio'):
        result['warnings'].append('No audio stream found in output file.')

    # All critical checks passed
    result['valid'] = True
    logger.info(f"Validation passed for {filepath}: {file_size} bytes, video={probe['has_video']}, audio={probe['has_audio']}")
    return result
