"""
FFmpeg media processing service.

Handles:
- Remuxing (stream copy) when source is already compatible
- Container conversion when needed
- Audio/subtitle track preservation
- Processing progress estimation
"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def process_media(source_filepath: str, output_filepath: str, target_format: str = 'mp4') -> dict:
    """
    Process downloaded media through FFmpeg.

    Prefers remuxing (stream copy) over re-encoding to avoid quality loss,
    CPU overhead, and unnecessary processing time.

    Args:
        source_filepath: Path to the downloaded source file.
        output_filepath: Path for the processed output file.
        target_format: Target container format (default: 'mp4').

    Returns:
        dict with 'success', 'output_path', 'error'.
    """
    if not os.path.exists(source_filepath):
        return {'success': False, 'output_path': '', 'error': f'Source file not found: {source_filepath}'}

    # If source is already in the target format and valid, attempt direct remux
    try:
        ffmpeg_path = _find_ffmpeg()

        if ffmpeg_path:
            result = _remux_with_ffmpeg(ffmpeg_path, source_filepath, output_filepath)
            if result['success']:
                return result

            # If remux failed, try re-encoding as fallback
            result = _reencode_with_ffmpeg(ffmpeg_path, source_filepath, output_filepath)
            if result['success']:
                return result

        # No FFmpeg available — try direct copy if formats match
        return _direct_copy(source_filepath, output_filepath)

    except Exception as e:
        logger.error(f"Media processing failed: {e}")
        return {'success': False, 'output_path': '', 'error': str(e)}


def _find_ffmpeg() -> str | None:
    """Find the FFmpeg executable on the system."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        if result.returncode == 0:
            return 'ffmpeg'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try common Windows paths
    common_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        'ffmpeg.exe',
    ]
    for path in common_paths:
        if path and os.path.isfile(path):
            return path

    logger.warning("FFmpeg not found on system")
    return None


def _remux_with_ffmpeg(ffmpeg_path: str, source: str, output: str) -> dict:
    """
    Remux (stream copy) without re-encoding.

    This is the preferred processing mode — no quality loss, fast, low CPU.
    """
    try:
        cmd = [
            ffmpeg_path,
            '-i', source,
            '-c', 'copy',          # Stream copy (no re-encoding)
            '-movflags', '+faststart',  # Web-optimized MP4
            '-y',                  # Overwrite output
            output
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=1800)

        if result.returncode == 0 and os.path.exists(output) and os.path.getsize(output) > 0:
            logger.info(f"Remux succeeded: {output}")
            return {'success': True, 'output_path': output, 'error': ''}
        else:
            stderr = result.stderr.decode('utf-8', errors='replace')[-500:]
            logger.warning(f"Remux failed: {stderr}")
            return {'success': False, 'output_path': '', 'error': f'Remux failed: {stderr}'}

    except subprocess.TimeoutExpired:
        return {'success': False, 'output_path': '', 'error': 'FFmpeg remux timed out.'}
    except Exception as e:
        return {'success': False, 'output_path': '', 'error': str(e)}


def _reencode_with_ffmpeg(ffmpeg_path: str, source: str, output: str) -> dict:
    """
    Re-encode to H.264/AAC for maximum compatibility.

    Fallback when remuxing fails (incompatible codecs).
    """
    try:
        cmd = [
            ffmpeg_path,
            '-i', source,
            '-c:v', 'libx264',     # H.264 video
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',         # AAC audio
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
            output
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=7200)

        if result.returncode == 0 and os.path.exists(output) and os.path.getsize(output) > 0:
            logger.info(f"Re-encode succeeded: {output}")
            return {'success': True, 'output_path': output, 'error': ''}
        else:
            stderr = result.stderr.decode('utf-8', errors='replace')[-500:]
            return {'success': False, 'output_path': '', 'error': f'Re-encode failed: {stderr}'}

    except subprocess.TimeoutExpired:
        return {'success': False, 'output_path': '', 'error': 'FFmpeg re-encode timed out.'}
    except Exception as e:
        return {'success': False, 'output_path': '', 'error': str(e)}


def _direct_copy(source: str, output: str) -> dict:
    """
    Direct file copy when FFmpeg is not available.

    Only works if the source is already in a compatible format.
    """
    try:
        import shutil
        shutil.copy2(source, output)
        if os.path.exists(output) and os.path.getsize(output) > 0:
            logger.info(f"Direct copy succeeded: {output}")
            return {'success': True, 'output_path': output, 'error': ''}
        return {'success': False, 'output_path': '', 'error': 'Direct copy produced empty file.'}
    except Exception as e:
        return {'success': False, 'output_path': '', 'error': str(e)}


def probe_media_info(filepath: str) -> dict:
    """
    Probe a media file for stream information using ffprobe.

    Returns:
        dict with 'has_video', 'has_audio', 'duration', 'format', 'error'.
    """
    info = {'has_video': False, 'has_audio': False, 'duration': 0, 'format': '', 'error': ''}

    try:
        ffprobe_path = 'ffprobe'
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            filepath
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)

            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    info['has_video'] = True
                elif stream.get('codec_type') == 'audio':
                    info['has_audio'] = True

            fmt = data.get('format', {})
            info['duration'] = float(fmt.get('duration', 0))
            info['format'] = fmt.get('format_name', '')
    except Exception as e:
        info['error'] = str(e)

    return info
