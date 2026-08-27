import re

def sanitize_filename(name: str) -> str:
    """Removes filesystem illegal characters from title strings."""
    return re.sub(r'[\\/*?:"<>|]', '', name).strip()

def generate_video_filename(media_type: str, title: str, year: str = None, season: int = None, episode: int = None, quality: str = '1080p', ext: str = 'mp4') -> str:
    """
    Generates deterministic, clean filenames according to Filvora Phase 11 specifications:
    - Movies: "Movie Name (Year) [Quality].ext"
    - Episodes: "Series Name S01E01 [Quality].ext"
    """
    clean_title = sanitize_filename(title)
    clean_quality = sanitize_filename(quality or '1080p')
    clean_ext = ext.lstrip('.') if ext else 'mp4'

    if media_type == 'tv' or (season is not None and episode is not None):
        s_num = season if season is not None else 1
        ep_num = episode if episode is not None else 1
        return f"{clean_title} S{s_num:02d}E{ep_num:02d} [{clean_quality}].{clean_ext}"

    # Movie
    year_str = f" ({year})" if year else ""
    return f"{clean_title}{year_str} [{clean_quality}].{clean_ext}"
