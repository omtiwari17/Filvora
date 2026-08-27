import time
import requests
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class PlaybackSource:
    url: str
    stream_type: str  # 'embed', 'hls', 'mp4'
    provider_id: str
    provider_name: str
    priority: int

class PlaybackProvider:
    id: str = "base"
    name: str = "Base Provider"
    priority: int = 100
    is_active: bool = True
    stream_type: str = "embed"
    health_check_url: Optional[str] = None

    def get_movie_url(self, tmdb_id: int) -> str:
        raise NotImplementedError

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        raise NotImplementedError

    def get_movie_source(self, tmdb_id: int) -> PlaybackSource:
        return PlaybackSource(
            url=self.get_movie_url(tmdb_id),
            stream_type=self.stream_type,
            provider_id=self.id,
            provider_name=self.name,
            priority=self.priority
        )

    def get_episode_source(self, tmdb_id: int, season: int, episode: int) -> PlaybackSource:
        return PlaybackSource(
            url=self.get_tv_url(tmdb_id, season, episode),
            stream_type=self.stream_type,
            provider_id=self.id,
            provider_name=self.name,
            priority=self.priority
        )

    def check_health(self) -> Dict[str, Any]:
        """Performs a quick non-blocking latency/status check."""
        target = self.health_check_url or self.get_movie_url(157336)
        start_time = time.time()
        status = "unknown"
        latency_ms = None
        error_detail = None
        try:
            r = requests.head(target, timeout=3, allow_redirects=True, headers={'User-Agent': 'Filvora/2.0'})
            latency_ms = round((time.time() - start_time) * 1000, 1)
            status = "healthy" if r.status_code < 500 else "degraded"
        except requests.Timeout:
            status = "timeout"
            error_detail = "Request timed out (>3000ms)"
        except Exception as e:
            status = "error"
            error_detail = str(e)

        return {
            "provider_id": self.id,
            "name": self.name,
            "priority": self.priority,
            "is_active": self.is_active,
            "status": status,
            "latency_ms": latency_ms,
            "error": error_detail,
            "checked_at": time.time()
        }


class VidLinkProvider(PlaybackProvider):
    id = "vidlink"
    name = "Server 1 (VidLink - Fast HD)"
    priority = 1
    health_check_url = "https://vidlink.pro"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://vidlink.pro/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}"


class AutoEmbedProvider(PlaybackProvider):
    id = "autoembed"
    name = "Server 2 (AutoEmbed)"
    priority = 2
    health_check_url = "https://autoembed.co"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://autoembed.co/movie/tmdb/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://autoembed.co/tv/tmdb/{tmdb_id}-{season}-{episode}"


class TwoEmbedProvider(PlaybackProvider):
    id = "2embed"
    name = "Server 3 (2Embed)"
    priority = 3
    health_check_url = "https://www.2embed.cc"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://www.2embed.cc/embed/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://www.2embed.cc/embedtv/{tmdb_id}&s={season}&e={episode}"


class NontonGoProvider(PlaybackProvider):
    id = "nontongo"
    name = "Server 4 (NontonGo)"
    priority = 4
    health_check_url = "https://www.NontonGo.win"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://www.NontonGo.win/embed/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://www.NontonGo.win/embed/tv/{tmdb_id}/{season}/{episode}"


class VidsrcProvider(PlaybackProvider):
    id = "vidsrc"
    name = "Server 5 (VidSrc)"
    priority = 5
    health_check_url = "https://vidsrc.me"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season={season}&episode={episode}"


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, PlaybackProvider] = {}
        # Register default providers
        for p in [VidLinkProvider(), AutoEmbedProvider(), TwoEmbedProvider(), NontonGoProvider(), VidsrcProvider()]:
            self.register(p)

    def register(self, provider: PlaybackProvider):
        self._providers[provider.id] = provider

    def get(self, provider_id: Optional[str] = None) -> PlaybackProvider:
        if provider_id and provider_id in self._providers:
            p = self._providers[provider_id]
            if p.is_active:
                return p
        ordered = self.get_ordered_providers()
        return ordered[0] if ordered else VidLinkProvider()

    def get_ordered_providers(self, preferred_id: Optional[str] = None) -> List[PlaybackProvider]:
        active = [p for p in self._providers.values() if p.is_active]
        active.sort(key=lambda x: x.priority)
        if preferred_id:
            preferred = [p for p in active if p.id == preferred_id]
            others = [p for p in active if p.id != preferred_id]
            return preferred + others
        return active

    def get_next_provider(self, current_provider_id: str) -> PlaybackProvider:
        ordered = self.get_ordered_providers()
        for idx, p in enumerate(ordered):
            if p.id == current_provider_id:
                next_idx = (idx + 1) % len(ordered)
                return ordered[next_idx]
        return ordered[0] if ordered else VidLinkProvider()

    def run_diagnostics(self) -> List[Dict[str, Any]]:
        results = []
        for p in self.get_ordered_providers():
            results.append(p.check_health())
        return results


# Global Registry Instance
registry = ProviderRegistry()
PROVIDERS = registry.get_ordered_providers()

def get_provider(provider_id: Optional[str] = None) -> PlaybackProvider:
    return registry.get(provider_id)
