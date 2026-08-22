class BaseVideoProvider:
    id = "base"
    name = "Base Provider"

    def get_movie_url(self, tmdb_id: int) -> str:
        raise NotImplementedError

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        raise NotImplementedError


class VidLinkProvider(BaseVideoProvider):
    id = "vidlink"
    name = "Server 1 (VidLink)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://vidlink.pro/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}"


class AutoEmbedProvider(BaseVideoProvider):
    id = "autoembed"
    name = "Server 2 (AutoEmbed)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://player.autoembed.cc/embed/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://player.autoembed.cc/embed/tv/{tmdb_id}/{season}/{episode}"


class VidSrcProvider(BaseVideoProvider):
    id = "vidsrc"
    name = "Server 3 (VidSrc)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://vidsrc.xyz/embed/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://vidsrc.xyz/embed/tv/{tmdb_id}/{season}/{episode}"


class MultiEmbedProvider(BaseVideoProvider):
    id = "multiembed"
    name = "Server 4 (MultiEmbed)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s={season}&e={episode}"


class SmashyStreamProvider(BaseVideoProvider):
    id = "smashy"
    name = "Server 5 (Smashy)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://player.smashy.stream/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://player.smashy.stream/tv/{tmdb_id}?s={season}&e={episode}"


# Registry of active providers
PROVIDERS = [
    VidLinkProvider(),
    AutoEmbedProvider(),
    VidSrcProvider(),
    MultiEmbedProvider(),
    SmashyStreamProvider(),
]

def get_provider(provider_id: str = None) -> BaseVideoProvider:
    if provider_id:
        for p in PROVIDERS:
            if p.id == provider_id:
                return p
    return PROVIDERS[0]
