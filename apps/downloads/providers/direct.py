"""
Direct Download Provider for authorized media streams.

Provides direct downloadable sources for public domain, licensed,
or authorized content streams.
"""
from apps.downloads.providers.base import DownloadProvider


class DirectDownloadProvider(DownloadProvider):
    """
    Authorized Direct Download Provider.
    """

    @property
    def name(self) -> str:
        return "Filvora Direct"

    @property
    def priority(self) -> int:
        return 1

    def supports_download(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> bool:
        # Supports all authorized catalog titles
        return True

    def get_available_qualities(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> list:
        return ['1080p', '720p', '480p']

    def get_downloadable_source(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None, quality: str = '1080p') -> dict:
        quality_sizes = {
            '1080p': 1024 * 1024 * 50,   # ~50 MB simulated payload
            '720p': 1024 * 1024 * 30,    # ~30 MB
            '480p': 1024 * 1024 * 15,    # ~15 MB
        }
        size = quality_sizes.get(quality, 1024 * 1024 * 30)

        return {
            'url': '',  # Handled locally via direct pipeline
            'headers': {'User-Agent': 'Filvora/2.0'},
            'quality': quality,
            'format': 'mp4',
            'estimated_size': size
        }
