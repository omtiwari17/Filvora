import os
import requests
from django.conf import settings

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        if not self.api_key and hasattr(settings, 'TMDB_API_KEY'):
            self.api_key = settings.TMDB_API_KEY
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Filvora/1.0 (Contact: admin@filvora.local)',
            'Accept': 'application/json'
        })

    def _get_mock_movies(self):
        return [
            {
                "id": 157336,
                "title": "Interstellar",
                "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
                "poster_path": "",
                "backdrop_path": ""
            },
            {
                "id": 438631,
                "title": "Dune",
                "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding...",
                "poster_path": "",
                "backdrop_path": ""
            }
        ]

    def _get_mock_series(self):
        return [
            {
                "id": 1399,
                "name": "Game of Thrones",
                "overview": "Seven noble families fight for control of the mythical land of Westeros.",
                "poster_path": "",
                "backdrop_path": ""
            },
            {
                "id": 66732,
                "name": "Stranger Things",
                "overview": "When a young boy vanishes, a small town uncovers a mystery...",
                "poster_path": "",
                "backdrop_path": ""
            }
        ]

    def get_trending_movies(self):
        if not self.api_key:
            return self._get_mock_movies()
        
        try:
            response = self.session.get(f"{self.BASE_URL}/trending/movie/day", params={"api_key": self.api_key}, timeout=5)
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException as e:
            print(f"TMDB Error (Movies): {e}")
            return self._get_mock_movies()

    def get_popular_series(self):
        if not self.api_key:
            return self._get_mock_series()
        
        try:
            response = self.session.get(f"{self.BASE_URL}/tv/popular", params={"api_key": self.api_key}, timeout=5)
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException as e:
            print(f"TMDB Error (Series): {e}")
            return self._get_mock_series()

    def get_movie(self, movie_id):
        if not self.api_key:
            return {"id": movie_id, "title": f"Mock Movie {movie_id}"}
        
        try:
            response = self.session.get(f"{self.BASE_URL}/movie/{movie_id}", params={"api_key": self.api_key}, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"TMDB Error (Movie {movie_id}): {e}")
            return {"id": movie_id, "title": f"Mock Movie {movie_id}"}

    def get_tv(self, tv_id):
        if not self.api_key:
            return {"id": tv_id, "name": f"Mock TV {tv_id}"}
        
        try:
            response = self.session.get(f"{self.BASE_URL}/tv/{tv_id}", params={"api_key": self.api_key}, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"TMDB Error (TV {tv_id}): {e}")
            return {"id": tv_id, "name": f"Mock TV {tv_id}"}
