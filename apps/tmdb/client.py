import os
import time
import json
import subprocess
import urllib.parse
import requests
from django.conf import settings

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    _cache = {}
    CACHE_TTL = 300  # 5 minutes in-memory cache

    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        if not self.api_key and hasattr(settings, 'TMDB_API_KEY'):
            self.api_key = settings.TMDB_API_KEY

    def _fetch(self, endpoint, params=None):
        if not params:
            params = {}
        
        # Check in-memory cache
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.CACHE_TTL:
                return cached_data

        if not self.api_key:
            return {}

        params['api_key'] = self.api_key
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}{endpoint}?{query_string}"

        # Method 1: Windows Schannel curl with --ssl-no-revoke and IPv4
        try:
            res = subprocess.run(
                ['curl.exe', '-s', '--ssl-no-revoke', '-4', '--connect-timeout', '4', url],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=6
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if not data.get('status_code'):  # Not an error response
                    self._cache[cache_key] = (data, time.time())
                    return data
        except Exception:
            pass

        # Method 2: Requests fallback
        try:
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                data = r.json()
                self._cache[cache_key] = (data, time.time())
                return data
        except Exception as e:
            print(f"TMDB Fetch Error for {endpoint}: {e}")

        return {}

    def get_trending_movies(self):
        data = self._fetch("/trending/movie/day")
        return data.get('results', self._get_mock_movies())

    def get_popular_movies(self, page=1):
        data = self._fetch("/movie/popular", {"page": page})
        return data.get('results', self._get_mock_movies())

    def get_popular_series(self, page=1):
        data = self._fetch("/tv/popular", {"page": page})
        return data.get('results', self._get_mock_series())

    def get_movie(self, movie_id):
        return self.get_movie_details(movie_id)

    def get_movie_details(self, movie_id):
        data = self._fetch(f"/movie/{movie_id}", {"append_to_response": "credits,recommendations"})
        if data and (data.get('title') or data.get('poster_path')):
            return data

        # Check mock data fallback
        for m in self._get_mock_movies():
            if m['id'] == int(movie_id):
                return m

        return {
            "id": movie_id,
            "title": f"Movie {movie_id}",
            "tagline": "A cinematic journey on Filvora.",
            "overview": "Embark on an unforgettable adventure with captivating performances, stunning visuals, and a compelling storyline.",
            "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
            "backdrop_path": "/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
            "runtime": 120,
            "vote_average": 7.5,
            "release_date": "2024-01-01",
            "genres": [{"id": 28, "name": "Action"}, {"id": 18, "name": "Drama"}],
            "credits": {"cast": []},
            "recommendations": {"results": []}
        }

    def get_tv(self, tv_id):
        return self.get_tv_details(tv_id)

    def get_tv_details(self, tv_id):
        data = self._fetch(f"/tv/{tv_id}", {"append_to_response": "credits,recommendations"})
        if data and (data.get('name') or data.get('poster_path')):
            return data

        # Check mock data fallback
        for s in self._get_mock_series():
            if s['id'] == int(tv_id):
                return s

        return {
            "id": tv_id,
            "name": f"Series {tv_id}",
            "tagline": "An extraordinary episodic journey.",
            "overview": "Follow an ensemble cast navigating intricate plots, unexpected twists, and gripping dramatic tension across every episode.",
            "poster_path": "/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
            "backdrop_path": "/2OMB0ynKlyIenMJWI2Dy9IWT4c.jpg",
            "number_of_seasons": 1,
            "number_of_episodes": 10,
            "vote_average": 8.0,
            "first_air_date": "2024-01-01",
            "genres": [{"id": 18, "name": "Drama"}, {"id": 10765, "name": "Sci-Fi & Fantasy"}],
            "seasons": [{"season_number": 1, "name": "Season 1", "episode_count": 10}],
            "credits": {"cast": []},
            "recommendations": {"results": []}
        }

    def get_tv_season(self, tv_id, season_number):
        data = self._fetch(f"/tv/{tv_id}/season/{season_number}")
        if data and data.get('episodes'):
            return data

        return {
            "season_number": season_number,
            "episodes": [
                {
                    "episode_number": i,
                    "name": f"Episode {i}",
                    "overview": f"The story intensifies as new revelations come to light in chapter {i} of Season {season_number}.",
                    "still_path": "",
                    "air_date": "2024-01-01",
                    "runtime": 50
                } for i in range(1, 11)
            ]
        }

    def search_multi(self, query):
        if not query or not query.strip():
            return []
        data = self._fetch("/search/multi", {"query": query.strip()})
        results = data.get('results', [])
        filtered = []
        for r in results:
            if r.get('media_type') in ['movie', 'tv']:
                r['display_title'] = r.get('title') or r.get('name')
                filtered.append(r)
        return filtered

    def _get_mock_movies(self):
        return [
            {
                "id": 157336,
                "title": "Interstellar",
                "tagline": "Mankind was born on Earth. It was never meant to die here.",
                "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
                "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                "backdrop_path": "/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
                "release_date": "2014-11-05",
                "runtime": 169,
                "vote_average": 8.4,
                "genres": [{"id": 12, "name": "Adventure"}, {"id": 18, "name": "Drama"}, {"id": 878, "name": "Science Fiction"}]
            },
            {
                "id": 438631,
                "title": "Dune",
                "tagline": "Beyond fear, destiny awaits.",
                "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
                "poster_path": "/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                "backdrop_path": "/lzWHmYdfeFiMIY4JaMmtR7GEli3.jpg",
                "release_date": "2021-09-15",
                "runtime": 155,
                "vote_average": 7.8,
                "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 12, "name": "Adventure"}]
            },
            {
                "id": 27205,
                "title": "Inception",
                "tagline": "Your mind is the scene of the crime.",
                "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets, is offered a chance to regain his old life as payment for a task considered to be impossible.",
                "poster_path": "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
                "backdrop_path": "/s3TBrRGB1jav7cUneYISv9NVIuu.jpg",
                "release_date": "2010-07-15",
                "runtime": 148,
                "vote_average": 8.4,
                "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}, {"id": 12, "name": "Adventure"}]
            }
        ]

    def _get_mock_series(self):
        return [
            {
                "id": 1399,
                "name": "Game of Thrones",
                "tagline": "Winter Is Coming",
                "overview": "Seven noble families fight for control of the mythical land of Westeros. Friction between the houses leads to full-scale war.",
                "poster_path": "/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
                "backdrop_path": "/2OMB0ynKlyIenMJWI2Dy9IWT4c.jpg",
                "first_air_date": "2011-04-17",
                "number_of_seasons": 8,
                "number_of_episodes": 73,
                "vote_average": 8.4,
                "genres": [{"id": 10765, "name": "Sci-Fi & Fantasy"}, {"id": 18, "name": "Drama"}, {"id": 10759, "name": "Action & Adventure"}],
                "seasons": [
                    {"season_number": 1, "name": "Season 1", "episode_count": 10},
                    {"season_number": 2, "name": "Season 2", "episode_count": 10},
                    {"season_number": 3, "name": "Season 3", "episode_count": 10}
                ]
            },
            {
                "id": 66732,
                "name": "Stranger Things",
                "tagline": "Every ending has a beginning.",
                "overview": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
                "poster_path": "/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
                "backdrop_path": "/56v2KjBlU4XaOv9rVYEQypROD7P.jpg",
                "first_air_date": "2016-07-15",
                "number_of_seasons": 4,
                "number_of_episodes": 34,
                "vote_average": 8.6,
                "genres": [{"id": 18, "name": "Drama"}, {"id": 10765, "name": "Sci-Fi & Fantasy"}, {"id": 9648, "name": "Mystery"}],
                "seasons": [
                    {"season_number": 1, "name": "Season 1", "episode_count": 8},
                    {"season_number": 2, "name": "Season 2", "episode_count": 9}
                ]
            }
        ]
