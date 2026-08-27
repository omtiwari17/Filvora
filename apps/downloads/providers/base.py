"""
Abstract base class for download providers.

A download provider represents an authorized source that explicitly supports
downloading content. Playback providers and download providers are separate
concepts — a playback provider is NOT automatically a download provider.
"""
from abc import ABC, abstractmethod


class DownloadProvider(ABC):
    """
    Base class for all authorized download providers.

    Each provider must implement:
    - name: Human-readable provider name
    - supports_download(): Whether this provider can download the given content
    - get_downloadable_source(): Returns a downloadable URL/stream info
    - get_available_qualities(): Returns list of available quality options
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this provider."""
        raise NotImplementedError

    @property
    def priority(self) -> int:
        """Priority for provider selection (lower = higher priority). Default: 100."""
        return 100

    @abstractmethod
    def supports_download(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> bool:
        """
        Check whether this provider can supply a downloadable source
        for the given content.

        Args:
            tmdb_id: TMDB content identifier.
            media_type: 'movie' or 'tv'.
            season: Season number (for TV episodes).
            episode: Episode number (for TV episodes).

        Returns:
            True if the provider can supply a downloadable source.
        """
        raise NotImplementedError

    @abstractmethod
    def get_downloadable_source(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None, quality: str = '1080p') -> dict:
        """
        Return download source information for the given content.

        Args:
            tmdb_id: TMDB content identifier.
            media_type: 'movie' or 'tv'.
            season: Season number (for TV episodes).
            episode: Episode number (for TV episodes).
            quality: Requested quality (e.g., '1080p', '720p').

        Returns:
            dict with keys:
                - 'url': Direct download URL or stream URL
                - 'headers': Optional dict of HTTP headers needed
                - 'quality': Actual quality of the source
                - 'format': Source format (e.g., 'mp4', 'mkv')
                - 'estimated_size': Estimated file size in bytes (0 if unknown)
        """
        raise NotImplementedError

    def get_available_qualities(self, tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> list:
        """
        Return list of available quality options for the given content.

        Returns:
            List of quality strings, e.g., ['1080p', '720p', '480p'].
            Default implementation returns common qualities.
        """
        return ['1080p', '720p', '480p']
