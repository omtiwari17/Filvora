"""
Download provider registry.

Manages registration and resolution of authorized download providers.
Providers are resolved by priority (lower number = higher priority).
"""
from apps.downloads.providers.base import DownloadProvider
from apps.downloads.providers.direct import DirectDownloadProvider

# Global provider registry initialized with default authorized providers
_PROVIDERS: list[DownloadProvider] = [DirectDownloadProvider()]


def register_provider(provider: DownloadProvider):
    """Register an authorized download provider."""
    if not isinstance(provider, DownloadProvider):
        raise TypeError(f"Expected DownloadProvider, got {type(provider).__name__}")
    _PROVIDERS.append(provider)
    _PROVIDERS.sort(key=lambda p: p.priority)


def get_providers() -> list[DownloadProvider]:
    """Return all registered providers sorted by priority."""
    return list(_PROVIDERS)


def find_provider(tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> DownloadProvider | None:
    """
    Find the highest-priority provider that supports downloading the given content.

    Returns:
        The best available DownloadProvider, or None if no provider supports this content.
    """
    for provider in _PROVIDERS:
        try:
            if provider.supports_download(tmdb_id, media_type, season, episode):
                return provider
        except Exception:
            continue
    return None


def get_available_qualities(tmdb_id: int, media_type: str, season: int = None, episode: int = None) -> list:
    """
    Get available download qualities from the best available provider.

    Returns:
        List of quality strings, or default ['1080p', '720p', '480p'] if no provider found.
    """
    provider = find_provider(tmdb_id, media_type, season, episode)
    if provider:
        return provider.get_available_qualities(tmdb_id, media_type, season, episode)
    return ['1080p', '720p', '480p']


def clear_providers():
    """Clear all registered providers (for testing)."""
    _PROVIDERS.clear()


def reset_default_providers():
    """Reset to default providers."""
    _PROVIDERS.clear()
    _PROVIDERS.append(DirectDownloadProvider())
