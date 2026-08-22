class BaseVideoProvider:
    id = "base"
    name = "Base Provider"

    def get_movie_url(self, tmdb_id: int) -> str:
        raise NotImplementedError

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        raise NotImplementedError


class VidLinkProvider(BaseVideoProvider):
    id = "vidlink"
    name = "Server 1 (VidLink - Fast HD)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://vidlink.pro/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}"


class AutoEmbedProvider(BaseVideoProvider):
    id = "autoembed"
    name = "Server 2 (AutoEmbed)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://autoembed.co/movie/tmdb/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://autoembed.co/tv/tmdb/{tmdb_id}-{season}-{episode}"


class TwoEmbedProvider(BaseVideoProvider):
    id = "2embed"
    name = "Server 3 (2Embed)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://www.2embed.cc/embed/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://www.2embed.cc/embedtv/{tmdb_id}&s={season}&e={episode}"


class NontonGoProvider(BaseVideoProvider):
    id = "nontongo"
    name = "Server 4 (NontonGo)"

    def get_movie_url(self, tmdb_id: int) -> str:
        return f"https://www.NontonGo.win/embed/movie/{tmdb_id}"

    def get_tv_url(self, tmdb_id: int, season: int, episode: int) -> str:
        return f"https://www.NontonGo.win/embed/tv/{tmdb_id}/{season}/{episode}"


# Active, verified providers
PROVIDERS = [
    VidLinkProvider(),
    AutoEmbedProvider(),
    TwoEmbedProvider(),
    NontonGoProvider(),
]

def get_provider(provider_id: str = None) -> BaseVideoProvider:
    if provider_id:
        for p in PROVIDERS:
            if p.id == provider_id:
                return p
    return PROVIDERS[0]
