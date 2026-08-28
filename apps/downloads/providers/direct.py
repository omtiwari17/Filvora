"""
Direct Download Provider for authorized media streams.

Provides direct downloadable sources for public domain, licensed,
or authorized content streams with explicit direct file URLs.
"""
from apps.downloads.providers.base import DownloadProvider


class DirectDownloadProvider(DownloadProvider):
    """
    Authorized Direct Download Provider for explicit file sources.
    """

    @property
    def name(self) -> str:
        return "Filvora Direct"

    @property
    def priority(self) -> int:
        return 2

    def supports_download(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> bool:
        # Explicit direct sources only
        return False

    def get_available_qualities(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> list:
        return ['1080p', '720p', '480p']

    def get_downloadable_source(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None, quality: str = '1080p') -> dict:
        return {
            'url': '',
            'headers': {'User-Agent': 'Filvora/2.0'},
            'quality': quality,
            'format': 'mp4',
            'estimated_size': 0
        }

