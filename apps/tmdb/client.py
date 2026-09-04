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
    CACHE_TTL = 900  # 15 minutes in-memory cache
    _session = None

    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        if not self.api_key and hasattr(settings, 'TMDB_API_KEY'):
            self.api_key = settings.TMDB_API_KEY
        if TMDBClient._session is None:
            TMDBClient._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=25, pool_maxsize=25, max_retries=1)
            TMDBClient._session.mount('https://', adapter)
            TMDBClient._session.mount('http://', adapter)

    def _fetch(self, endpoint, params=None):
        req_params = dict(params) if params else {}
        
        # Check in-memory cache
        cache_key = f"{endpoint}:{json.dumps(req_params, sort_keys=True)}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.CACHE_TTL:
                return cached_data

        if not self.api_key:
            return {}

        req_params['api_key'] = self.api_key
        query_string = urllib.parse.urlencode(req_params)
        url = f"{self.BASE_URL}{endpoint}?{query_string}"

        # Method 1: Requests with persistent keep-alive connection pool (Fastest, ~100-200ms)
        try:
            r = self._session.get(url, timeout=4.5)
            if r.status_code == 200:
                data = r.json()
                self._cache[cache_key] = (data, time.time())
                return data
        except Exception:
            pass

        # Method 2: Windows Schannel curl fallback if requests encounters SSL/network glitch
        try:
            res = subprocess.run(
                ['curl.exe', '-s', '--ssl-no-revoke', '-4', '--connect-timeout', '4', url],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if not data.get('status_code'):  # Not an error response
                    self._cache[cache_key] = (data, time.time())
                    return data
        except Exception:
            pass

        return {}

    _RATING_CACHE = {}

    def _extract_movie_rating(self, data):
        if not data:
            return None
        releases = data.get('release_dates', {}).get('results', [])
        if not releases and isinstance(data.get('results'), list):
            releases = data.get('results', [])

        # Priority 1: US certification
        for r in releases:
            if isinstance(r, dict) and r.get('iso_3166_1') == 'US':
                for d in r.get('release_dates', []):
                    cert = d.get('certification')
                    if cert and cert.strip():
                        return cert.strip()
        # Priority 2: Any available certification
        for r in releases:
            if isinstance(r, dict):
                for d in r.get('release_dates', []):
                    cert = d.get('certification')
                    if cert and cert.strip():
                        return cert.strip()
        # Fallback based on adult / genres
        if data.get('adult'):
            return '18+'
        genre_ids = [g.get('id') if isinstance(g, dict) else g for g in data.get('genres', [])]
        if any(gid in [16, 10751] for gid in genre_ids):
            return 'PG'
        if any(gid in [27, 80] for gid in genre_ids):
            return 'R'
        return 'PG-13'

    def _extract_tv_rating(self, data):
        if not data:
            return None
        ratings = data.get('content_ratings', {}).get('results', [])
        if not ratings and isinstance(data.get('results'), list):
            ratings = data.get('results', [])

        for r in ratings:
            if isinstance(r, dict) and r.get('iso_3166_1') == 'US':
                rating = r.get('rating')
                if rating and rating.strip():
                    return rating.strip()
        for r in ratings:
            if isinstance(r, dict):
                rating = r.get('rating')
                if rating and rating.strip():
                    return rating.strip()
        if data.get('adult'):
            return 'TV-MA'
        genre_ids = [g.get('id') if isinstance(g, dict) else g for g in data.get('genres', [])]
        if any(gid in [16, 10762] for gid in genre_ids):
            return 'TV-PG'
        if any(gid in [18, 80, 10768] for gid in genre_ids):
            return 'TV-MA'
        return 'TV-14'

    def get_content_rating(self, tmdb_id, media_type='movie'):
        if not tmdb_id:
            return None
        cache_key = f"{media_type}:{tmdb_id}"
        if cache_key in self._RATING_CACHE:
            return self._RATING_CACHE[cache_key]

        try:
            if media_type == 'movie':
                data = self._fetch(f"/movie/{tmdb_id}/release_dates")
                rating = self._extract_movie_rating(data) if data else None
            else:
                data = self._fetch(f"/tv/{tmdb_id}/content_ratings")
                rating = self._extract_tv_rating(data) if data else None

            if rating and rating in ['G', 'PG', 'PG-13', 'R', 'NC-17', '18+', 'TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA']:
                self._RATING_CACHE[cache_key] = rating
                return rating
        except Exception:
            pass

        return None

    def _attach_age_rating(self, item, media_type='movie'):
        if not item:
            return item
        if item.get('age_rating'):
            return item

        item_id = item.get('id')
        if item_id:
            cache_key = f"{media_type}:{item_id}"
            if cache_key in self._RATING_CACHE:
                item['age_rating'] = self._RATING_CACHE[cache_key]
                return item

            # Query official certification from TMDB
            real_rating = self.get_content_rating(item_id, media_type)
            if real_rating:
                item['age_rating'] = real_rating
                return item

        if media_type == 'movie':
            if item.get('adult'):
                item['age_rating'] = '18+'
            else:
                genre_ids = item.get('genre_ids', [])
                if any(gid in [16, 10751] for gid in genre_ids):
                    item['age_rating'] = 'PG'
                elif any(gid in [27, 80] for gid in genre_ids):
                    item['age_rating'] = 'R'
                else:
                    item['age_rating'] = 'PG-13'
        else:
            if item.get('adult'):
                item['age_rating'] = 'TV-MA'
            else:
                genre_ids = item.get('genre_ids', [])
                if any(gid in [16, 10762] for gid in genre_ids):
                    item['age_rating'] = 'TV-PG'
                elif any(gid in [18, 80, 10768] for gid in genre_ids):
                    item['age_rating'] = 'TV-MA'
                else:
                    item['age_rating'] = 'TV-14'

        if item_id and item.get('age_rating'):
            self._RATING_CACHE[f"{media_type}:{item_id}"] = item['age_rating']

        return item

    def get_trending_movies(self):
        data = self._fetch("/trending/movie/day")
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_popular_movies(self, page=1):
        data = self._fetch("/movie/popular", {"page": page})
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_top_rated_movies(self):
        data = self._fetch("/movie/top_rated")
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_popular_series(self, page=1):
        data = self._fetch("/tv/popular", {"page": page})
        results = data.get('results', self._get_mock_series())
        clean = [s for s in results if not any(g in [10763, 10767] for g in s.get('genre_ids', []))]
        return [self._attach_age_rating(s, 'tv') for s in clean]

    def get_top_rated_series(self):
        data = self._fetch("/tv/top_rated")
        results = data.get('results', self._get_mock_series())
        clean = [s for s in results if not any(g in [10763, 10767] for g in s.get('genre_ids', []))]
        return [self._attach_age_rating(s, 'tv') for s in clean]

    def get_action_movies(self):
        data = self._fetch("/discover/movie", {"with_genres": "28"})
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_scifi_movies(self):
        data = self._fetch("/discover/movie", {"with_genres": "878"})
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_animation_movies(self):
        data = self._fetch("/discover/movie", {"with_genres": "16"})
        results = data.get('results', self._get_mock_movies())
        return [self._attach_age_rating(m, 'movie') for m in results]

    def get_movie_videos(self, movie_id):
        """Fetch official videos (trailers, teasers, featurettes) for a movie."""
        return self._fetch(f"/movie/{movie_id}/videos")

    def get_tv_videos(self, tv_id, season=None, episode=None):
        """Fetch official videos for a TV series or episode."""
        if season is not None and episode is not None:
            return self._fetch(f"/tv/{tv_id}/season/{season}/episode/{episode}/videos")
        elif season is not None:
            return self._fetch(f"/tv/{tv_id}/season/{season}/videos")
        return self._fetch(f"/tv/{tv_id}/videos")

    def extract_official_trailer(self, videos_data):
        """Extract the best YouTube trailer key from TMDB videos payload."""
        if not videos_data:
            return None
        videos = videos_data.get('results', []) if isinstance(videos_data, dict) else videos_data
        if not isinstance(videos, list):
            return None

        youtube_vids = [v for v in videos if isinstance(v, dict) and v.get('site') == 'YouTube' and v.get('key')]
        if not youtube_vids:
            return None

        # Priority 1: Official Trailer in English
        for v in youtube_vids:
            if v.get('type') == 'Trailer' and v.get('official') and v.get('iso_639_1') == 'en':
                return v.get('key')

        # Priority 2: Any Official Trailer
        for v in youtube_vids:
            if v.get('type') == 'Trailer' and v.get('official'):
                return v.get('key')

        # Priority 3: Any Trailer
        for v in youtube_vids:
            if v.get('type') == 'Trailer':
                return v.get('key')

        # Priority 4: Official Teaser
        for v in youtube_vids:
            if v.get('type') == 'Teaser' and v.get('official'):
                return v.get('key')

        # Priority 5: Any Teaser
        for v in youtube_vids:
            if v.get('type') == 'Teaser':
                return v.get('key')

        return youtube_vids[0].get('key')

    def get_official_trailer(self, tmdb_id, media_type='movie'):
        """Fetch and extract official trailer key for a movie or TV show."""
        if str(tmdb_id) in ["1744462", "1222222"]:
            return "QdBZY2fkU-0"
        if media_type == 'tv':
            v_data = self.get_tv_videos(tmdb_id)
        else:
            v_data = self.get_movie_videos(tmdb_id)
        return self.extract_official_trailer(v_data)

    def _fetch_paginated_24(self, endpoint, base_params, page=1, media_type='movie', kids_only=False, exclude_genres=None):
        try:
            curr_page = max(1, int(page or 1))
        except (ValueError, TypeError):
            curr_page = 1

        target_count = 24
        start_idx = (curr_page - 1) * target_count
        tmdb_start_page = max(1, (start_idx // 20) + 1)
        offset = start_idx - (tmdb_start_page - 1) * 20

        # For TV, always exclude news (10763) and talk shows (10767) unless specified otherwise
        if media_type == 'tv' and exclude_genres is None:
            exclude_genres = {10763, 10767}
        elif exclude_genres is None:
            exclude_genres = set()
        elif isinstance(exclude_genres, (list, tuple)):
            exclude_genres = set(exclude_genres)

        raw_results = []
        seen_ids = set()
        for p_num in range(tmdb_start_page, tmdb_start_page + 3):
            p_params = dict(base_params)
            p_params['page'] = p_num
            data = self._fetch(endpoint, p_params)
            res = data.get('results', [])
            if not res:
                break
            for item in res:
                iid = item.get('id')
                if not iid or iid in seen_ids:
                    continue
                seen_ids.add(iid)
                gids = item.get('genre_ids') or []
                if exclude_genres and any(g in exclude_genres for g in gids):
                    continue
                item['media_type'] = media_type
                item['display_title'] = item.get('title') or item.get('name') or f"Title {item.get('id')}"
                item['release_year'] = (item.get('release_date') or item.get('first_air_date') or '')[:4]
                self._attach_age_rating(item, media_type)
                if kids_only and item.get('age_rating') in ['R', 'NC-17', 'TV-MA', '18+']:
                    continue
                raw_results.append(item)
            if len(raw_results) >= (offset + target_count):
                break

        sliced = raw_results[offset : offset + target_count]
        if not sliced and raw_results:
            sliced = raw_results[:target_count]

        # Only fallback to mock if no results were obtained at all and API key is missing
        if not sliced and not self.api_key:
            mock_list = self._get_mock_movies() if media_type == 'movie' else self._get_mock_series()
            for m in mock_list:
                m['media_type'] = media_type
                m['display_title'] = m.get('title') or m.get('name') or f"Title {m.get('id')}"
                m['release_year'] = (m.get('release_date') or m.get('first_air_date') or '')[:4]
                self._attach_age_rating(m, media_type)
            return mock_list[:target_count]

        return sliced

    def get_movies_catalog(self, category='popular', genre_id=None, sort_by='popularity.desc', page=1, kids_only=False, audience=None):
        import datetime
        today_str = datetime.date.today().isoformat()
        has_genre = bool(genre_id)
        has_audience = bool(audience and audience != 'all')

        if category == 'trending':
            if not has_genre and not has_audience:
                return self._fetch_paginated_24("/trending/movie/day", {}, page=page, media_type='movie', kids_only=kids_only)
            return self.discover_content(
                media_type='movie',
                genre_id=genre_id,
                sort_by='popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience
            )

        elif category == 'top_rated':
            top_sort = sort_by if sort_by and sort_by != 'popularity.desc' else 'vote_average.desc'
            return self.discover_content(
                media_type='movie',
                genre_id=genre_id,
                sort_by=top_sort,
                page=page,
                kids_only=kids_only,
                audience=audience
            )

        elif category == 'now_playing':
            if not has_genre and not has_audience:
                return self._fetch_paginated_24("/movie/now_playing", {'region': 'US'}, page=page, media_type='movie', kids_only=kids_only)
            d45_str = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
            return self.discover_content(
                media_type='movie',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                date_gte=d45_str,
                date_lte=today_str
            )

        elif category == 'upcoming':
            return self.discover_content(
                media_type='movie',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                date_gte=today_str
            )

        else:  # popular
            return self.discover_content(
                media_type='movie',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience
            )

    def get_series_catalog(self, category='popular', genre_id=None, sort_by='popularity.desc', page=1, kids_only=False, audience=None):
        import datetime
        today_str = datetime.date.today().isoformat()
        has_genre = bool(genre_id)
        has_audience = bool(audience and audience != 'all')

        if category == 'trending':
            if not has_genre and not has_audience:
                return self._fetch_paginated_24("/trending/tv/day", {}, page=page, media_type='tv', kids_only=kids_only)
            return self.discover_content(
                media_type='tv',
                genre_id=genre_id,
                sort_by='popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                without_genres='10763,10767'
            )

        elif category == 'top_rated':
            top_sort = sort_by if sort_by and sort_by != 'popularity.desc' else 'vote_average.desc'
            return self.discover_content(
                media_type='tv',
                genre_id=genre_id,
                sort_by=top_sort,
                page=page,
                kids_only=kids_only,
                audience=audience,
                without_genres='10763,10767'
            )

        elif category == 'on_the_air':
            if not has_genre and not has_audience:
                return self._fetch_paginated_24("/tv/on_the_air", {}, page=page, media_type='tv', kids_only=kids_only)
            d7_before = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
            d7_after = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
            return self.discover_content(
                media_type='tv',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                air_date_gte=d7_before,
                air_date_lte=d7_after
            )

        elif category == 'airing_today':
            if not has_genre and not has_audience:
                return self._fetch_paginated_24("/tv/airing_today", {}, page=page, media_type='tv', kids_only=kids_only)
            return self.discover_content(
                media_type='tv',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                air_date_gte=today_str,
                air_date_lte=today_str
            )

        else:  # popular
            return self.discover_content(
                media_type='tv',
                genre_id=genre_id,
                sort_by=sort_by or 'popularity.desc',
                page=page,
                kids_only=kids_only,
                audience=audience,
                without_genres='10763,10767'
            )


    def get_movie(self, movie_id):
        return self.get_movie_details(movie_id)

    def get_movie_details(self, movie_id):
        if str(movie_id) in ["1744462", "1222222"]:
            data = self._fetch(f"/movie/{movie_id}", {"append_to_response": "credits,recommendations,release_dates,videos"})
            if data and (data.get('title') or data.get('poster_path')):
                data['age_rating'] = self._extract_movie_rating(data) or '18+'
                data['trailer_key'] = self.extract_official_trailer(data.get('videos')) or "QdBZY2fkU-0"
                return data
            return self._get_gta_vi_special()

        data = self._fetch(f"/movie/{movie_id}", {"append_to_response": "credits,recommendations,release_dates,videos"})
        if data and (data.get('title') or data.get('poster_path')):
            data['age_rating'] = self._extract_movie_rating(data)
            if data['age_rating']:
                self._RATING_CACHE[f"movie:{movie_id}"] = data['age_rating']
            if 'recommendations' in data and 'results' in data['recommendations']:
                data['recommendations']['results'] = [
                    self._attach_age_rating(r, 'movie') for r in data['recommendations']['results']
                ]
            data['trailer_key'] = self.extract_official_trailer(data.get('videos'))
            return data

        # Check mock data fallback
        for m in self._get_mock_movies():
            if m['id'] == int(movie_id):
                m['age_rating'] = m.get('age_rating', 'PG-13')
                self._RATING_CACHE[f"movie:{movie_id}"] = m['age_rating']
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
            "age_rating": "PG-13",
            "genres": [{"id": 28, "name": "Action"}, {"id": 18, "name": "Drama"}],
            "credits": {"cast": []},
            "recommendations": {"results": []},
            "trailer_key": None
        }

    def get_collection(self, collection_id):
        """Fetch full franchise collection details with chronologically ordered movie parts."""
        if not collection_id:
            return None
        data = self._fetch(f"/collection/{collection_id}")
        if not data or not isinstance(data, dict) or not data.get('parts'):
            return self._get_mock_collection(collection_id)
        
        parts = data.get('parts', [])
        parts.sort(key=lambda x: x.get('release_date') or '9999-99-99')
        for idx, part in enumerate(parts, 1):
            part['media_type'] = 'movie'
            part['display_title'] = part.get('title') or f"Part {idx}"
            part['release_year'] = (part.get('release_date') or '')[:4]
            part['franchise_order'] = idx
            self._attach_age_rating(part, 'movie')
            
        data['parts'] = parts
        data['total_parts'] = len(parts)
        return data

    def _get_mock_collection(self, collection_id):
        return {
            "id": int(collection_id) if str(collection_id).isdigit() else 1,
            "name": "The Cinematic Saga Collection",
            "overview": "An epic journey chronicling every installment of the iconic franchise.",
            "poster_path": "/sm7rZZivZm2NhJDucFf3gpfFdVt.jpg",
            "backdrop_path": "/fSwYa5q2xRkBoOOjueLpkLf3N1m.jpg",
            "parts": [
                {
                    "id": 101,
                    "title": "Saga: Chapter 1",
                    "display_title": "Saga: Chapter 1",
                    "release_date": "2021-01-01",
                    "release_year": "2021",
                    "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                    "vote_average": 8.1,
                    "age_rating": "PG-13",
                    "franchise_order": 1,
                    "media_type": "movie"
                },
                {
                    "id": 102,
                    "title": "Saga: Chapter 2",
                    "display_title": "Saga: Chapter 2",
                    "release_date": "2023-06-15",
                    "release_year": "2023",
                    "poster_path": "/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
                    "vote_average": 8.5,
                    "age_rating": "PG-13",
                    "franchise_order": 2,
                    "media_type": "movie"
                }
            ],
            "total_parts": 2
        }

    def get_tv(self, tv_id):
        return self.get_tv_details(tv_id)

    def get_tv_details(self, tv_id):
        data = self._fetch(f"/tv/{tv_id}", {"append_to_response": "credits,recommendations,content_ratings,videos"})
        if data and (data.get('name') or data.get('poster_path')):
            data['age_rating'] = self._extract_tv_rating(data)
            if data['age_rating']:
                self._RATING_CACHE[f"tv:{tv_id}"] = data['age_rating']
            if 'recommendations' in data and 'results' in data['recommendations']:
                data['recommendations']['results'] = [
                    self._attach_age_rating(r, 'tv') for r in data['recommendations']['results']
                ]
            data['trailer_key'] = self.extract_official_trailer(data.get('videos'))
            return data

        # Check mock data fallback
        for s in self._get_mock_series():
            if s['id'] == int(tv_id):
                s['age_rating'] = s.get('age_rating', 'TV-MA')
                self._RATING_CACHE[f"tv:{tv_id}"] = s['age_rating']
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
            "age_rating": "TV-MA",
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

    def search_multi_paginated(self, query, page=1):
        if not query or not query.strip():
            return {'results': [], 'total_pages': 1, 'total_results': 0}
        data = self._fetch("/search/multi", {"query": query.strip(), "page": page})
        results = data.get('results', [])
        total_pages = data.get('total_pages', 1)
        total_results = data.get('total_results', len(results))
        
        filtered = []
        seen_ids = set()
        seen_titles = set()
        for r in results:
            if r.get('media_type') in ['movie', 'tv']:
                item_id = r.get('id')
                item_title = (r.get('title') or r.get('name') or '').strip().lower()
                if item_id in seen_ids or (item_title and item_title in seen_titles):
                    continue
                seen_ids.add(item_id)
                if item_title:
                    seen_titles.add(item_title)
                r['display_title'] = r.get('title') or r.get('name')
                r['release_year'] = (r.get('release_date') or r.get('first_air_date') or '')[:4]
                self._attach_age_rating(r, r.get('media_type'))
                filtered.append(r)
        
        q_lower = query.lower()
        if any(term in q_lower for term in ['grand theft', 'gta', 'gta6', 'gta 6', 'gta vi', 'extended look', 'vice city', 'leonida', 'rockstar']):
            if not any(f.get('id') in [1744462, 1222222] or 'grand theft auto vi' in (f.get('title') or f.get('name') or '').lower() for f in filtered):
                gta = self._get_gta_vi_special()
                filtered.insert(0, gta)
                
        return {
            'results': filtered,
            'total_pages': total_pages,
            'total_results': total_results
        }

    def search_multi(self, query, page=1):
        return self.search_multi_paginated(query, page=page)['results']

    def search_categorized(self, query):
        if not query or not query.strip():
            return {'movies': [], 'series': [], 'people': []}
        data = self._fetch("/search/multi", {"query": query.strip()})
        results = data.get('results', [])
        categorized = {'movies': [], 'series': [], 'people': []}
        seen_movie_titles = set()
        for r in results:
            mtype = r.get('media_type')
            if mtype == 'movie':
                t_lower = (r.get('title') or '').strip().lower()
                if t_lower in seen_movie_titles:
                    continue
                seen_movie_titles.add(t_lower)
                r['display_title'] = r.get('title', 'Unknown Movie')
                r['release_year'] = (r.get('release_date') or '')[:4]
                self._attach_age_rating(r, 'movie')
                categorized['movies'].append(r)
            elif mtype == 'tv':
                r['display_title'] = r.get('name', 'Unknown Series')
                r['release_year'] = (r.get('first_air_date') or '')[:4]
                self._attach_age_rating(r, 'tv')
                categorized['series'].append(r)
            elif mtype == 'person':
                r['display_title'] = r.get('name', 'Unknown Person')
                known_titles = [k.get('title') or k.get('name') for k in r.get('known_for', []) if (k.get('title') or k.get('name'))]
                r['known_for_text'] = ", ".join(known_titles[:2]) if known_titles else r.get('known_for_department', 'Acting')
                categorized['people'].append(r)

        q_lower = query.lower()
        if any(term in q_lower for term in ['grand theft', 'gta', 'gta6', 'gta 6', 'gta vi', 'extended look', 'vice city', 'leonida', 'rockstar']):
            if not any(m.get('id') in [1744462, 1222222] or 'grand theft auto vi' in (m.get('title') or '').lower() for m in categorized['movies']):
                gta = self._get_gta_vi_special()
                categorized['movies'].insert(0, gta)

        return categorized

    MOVIE_TO_TV_GENRE_MAP = {
        28: 10759,     # Action -> Action & Adventure
        12: 10759,     # Adventure -> Action & Adventure
        878: 10765,    # Sci-Fi -> Sci-Fi & Fantasy
        14: 10765,     # Fantasy -> Sci-Fi & Fantasy
        27: 9648,      # Horror -> Mystery
        53: 80,        # Thriller -> Crime
        10749: 18,     # Romance -> Drama
        10752: 10768,  # War -> War & Politics
    }
    TV_TO_MOVIE_GENRE_MAP = {
        10759: 28,     # Action & Adventure -> Action
        10765: 878,    # Sci-Fi & Fantasy -> Sci-Fi
        10768: 10752,  # War & Politics -> War
        10762: 10751,  # Kids -> Family
        10764: 99,     # Reality -> Documentary
    }

    def _resolve_genre_for_media_type(self, genre_id, media_type='movie'):
        if not genre_id:
            return None
        try:
            gid = int(genre_id)
        except (ValueError, TypeError):
            return genre_id

        if media_type == 'tv':
            return self.MOVIE_TO_TV_GENRE_MAP.get(gid, gid)
        elif media_type == 'movie':
            return self.TV_TO_MOVIE_GENRE_MAP.get(gid, gid)
        return gid

    def get_genres_list(self, media_type='movie'):
        if media_type == 'tv':
            return [
                {"id": 10759, "name": "Action & Adventure", "slug": "action"},
                {"id": 16, "name": "Animation", "slug": "animation"},
                {"id": 35, "name": "Comedy", "slug": "comedy"},
                {"id": 80, "name": "Crime", "slug": "crime"},
                {"id": 99, "name": "Documentary", "slug": "documentary"},
                {"id": 18, "name": "Drama", "slug": "drama"},
                {"id": 10751, "name": "Family", "slug": "family"},
                {"id": 10762, "name": "Kids", "slug": "kids"},
                {"id": 9648, "name": "Mystery", "slug": "mystery"},
                {"id": 10764, "name": "Reality", "slug": "reality"},
                {"id": 10765, "name": "Sci-Fi & Fantasy", "slug": "scifi"},
                {"id": 10768, "name": "War & Politics", "slug": "war"},
                {"id": 37, "name": "Western", "slug": "western"},
            ]
        return [
            {"id": 28, "name": "Action", "slug": "action"},
            {"id": 12, "name": "Adventure", "slug": "adventure"},
            {"id": 16, "name": "Animation", "slug": "animation"},
            {"id": 35, "name": "Comedy", "slug": "comedy"},
            {"id": 80, "name": "Crime", "slug": "crime"},
            {"id": 99, "name": "Documentary", "slug": "documentary"},
            {"id": 18, "name": "Drama", "slug": "drama"},
            {"id": 10751, "name": "Family", "slug": "family"},
            {"id": 14, "name": "Fantasy", "slug": "fantasy"},
            {"id": 27, "name": "Horror", "slug": "horror"},
            {"id": 9648, "name": "Mystery", "slug": "mystery"},
            {"id": 10749, "name": "Romance", "slug": "romance"},
            {"id": 878, "name": "Sci-Fi", "slug": "scifi"},
            {"id": 53, "name": "Thriller", "slug": "thriller"},
            {"id": 10752, "name": "War", "slug": "war"},
            {"id": 37, "name": "Western", "slug": "western"},
        ]

    def discover_content(self, media_type='movie', genre_id=None, year=None, min_rating=None, mood=None, language=None, certification=None, kids_only=False, sort_by='popularity.desc', page=1, without_genres=None, audience=None, date_gte=None, date_lte=None, air_date_gte=None, air_date_lte=None):
        import datetime
        today_str = datetime.date.today().isoformat()
        sort_by = sort_by or "popularity.desc"

        # Adaptive vote thresholds for accuracy and high-quality titles
        if date_gte and date_gte >= today_str:
            default_vote_floor = 0
        elif sort_by == 'vote_average.desc':
            default_vote_floor = 300 if media_type == 'movie' else 150
        elif sort_by in ['popularity.desc', '']:
            default_vote_floor = 80 if media_type == 'movie' else 40
        else:
            default_vote_floor = 10 if media_type == 'movie' else 5

        params = {
            "page": page,
            "sort_by": sort_by,
            "vote_count.gte": default_vote_floor,
            "include_adult": 'false',
        }

        # Prevent unreleased/announced placeholder entries from polluting popular & newest catalogs
        if sort_by in ['popularity.desc', 'primary_release_date.desc', 'first_air_date.desc']:
            if not date_gte or date_gte < today_str:
                if media_type == 'movie':
                    params['primary_release_date.lte'] = today_str
                else:
                    params['first_air_date.lte'] = today_str

        # Mood mappings (media-aware, using TMDB pipe OR operator)
        mood_map_movie = {
            'adrenaline': '28|12|53',
            'mind_bending': '878|9648|18',
            'relax': '35|10751',
            'funny': '35',
            'emotional': '18|10749',
            'scary': '27|53',
            'escape_reality': '14|878|12',
        }
        mood_map_tv = {
            'adrenaline': '10759|80',
            'mind_bending': '10765|9648|18',
            'relax': '35|10751|10762',
            'funny': '35',
            'emotional': '18|10766',
            'scary': '9648',
            'escape_reality': '10765|10759',
        }
        mood_map = mood_map_movie if media_type == 'movie' else mood_map_tv

        # Genre & mood resolution (explicit genre takes precedence)
        if genre_id:
            resolved_genre = self._resolve_genre_for_media_type(genre_id, media_type)
            params['with_genres'] = str(resolved_genre)
        elif mood and mood in mood_map:
            params['with_genres'] = mood_map[mood]

        # Audience modes (All, Live-Action, Kids & Family, Mature)
        if audience == 'live_action':
            # Exclude toddler/children animation so Comedy shows actual live-action comedy!
            excluded = '16,10751' if media_type == 'movie' else '16,10751,10762'
            without_genres = f"{without_genres},{excluded}" if without_genres else excluded
        elif audience == 'kids_family':
            if not params.get('with_genres'):
                params['with_genres'] = '10751|16' if media_type == 'movie' else '10751|10762'
            params['certification_country'] = 'US'
            params['certification.lte'] = 'PG' if media_type == 'movie' else 'TV-PG'
        elif audience == 'mature':
            params['certification_country'] = 'US'
            params['certification'] = 'R' if media_type == 'movie' else 'TV-MA'

        if media_type == 'tv':
            tv_excluded = '10763,10767'
            without_genres = f"{without_genres},{tv_excluded}" if without_genres else tv_excluded

        if without_genres:
            params['without_genres'] = str(without_genres)

        if year:
            if media_type == 'movie':
                params['primary_release_year'] = str(year)
            else:
                params['first_air_date_year'] = str(year)

        if date_gte:
            if media_type == 'movie':
                params['primary_release_date.gte'] = str(date_gte)
            else:
                params['first_air_date.gte'] = str(date_gte)

        if date_lte:
            if media_type == 'movie':
                params['primary_release_date.lte'] = str(date_lte)
            else:
                params['first_air_date.lte'] = str(date_lte)

        if air_date_gte:
            params['air_date.gte'] = str(air_date_gte)

        if air_date_lte:
            params['air_date.lte'] = str(air_date_lte)

        if min_rating:
            params['vote_average.gte'] = str(min_rating)

        if language:
            params['with_original_language'] = str(language)

        # Certification handling with cross-media normalization
        if certification:
            params['certification_country'] = 'US'
            cert_str = str(certification).strip().upper()
            if media_type == 'tv':
                if cert_str in ['R', '18+', 'TV-MA']:
                    params['certification'] = 'TV-MA'
                elif cert_str in ['PG-13', 'TV-14']:
                    params['certification'] = 'TV-14'
                elif cert_str in ['PG', 'TV-PG']:
                    params['certification'] = 'TV-PG'
                elif cert_str in ['G', 'TV-G', 'TV-Y', 'TV-Y7']:
                    params['certification'] = 'TV-G|TV-Y'
                else:
                    params['certification'] = cert_str
            else:
                if cert_str in ['TV-MA', '18+', 'R']:
                    params['certification'] = 'R'
                elif cert_str in ['TV-14', 'PG-13']:
                    params['certification'] = 'PG-13'
                elif cert_str in ['TV-PG', 'PG']:
                    params['certification'] = 'PG'
                elif cert_str in ['TV-G', 'G', 'TV-Y']:
                    params['certification'] = 'G'
                else:
                    params['certification'] = cert_str
        elif kids_only:
            params['certification_country'] = 'US'
            params['certification.lte'] = 'PG' if media_type == 'movie' else 'TV-PG'
            params['include_adult'] = 'false'

        endpoint = "/discover/movie" if media_type == 'movie' else "/discover/tv"
        return self._fetch_paginated_24(endpoint, params, page=page, media_type=media_type, kids_only=kids_only)

    def get_surprise_title(self, media_type='movie', genre_id=None, mood=None):
        import random
        results = self.discover_content(media_type=media_type, genre_id=genre_id, mood=mood, min_rating=7.0)
        if results:
            return random.choice(results[:15])
        fallback = self._get_mock_movies()[0]
        fallback['media_type'] = 'movie'
        return fallback

    def get_person(self, person_id):
        endpoint = f"/person/{person_id}"
        params = {"append_to_response": "combined_credits"}
        data = self._fetch(endpoint, params)
        if not data or 'name' not in data:
            return {
                "id": person_id,
                "name": "Featured Artist",
                "biography": "Information and filmography for this artist.",
                "profile_path": None,
                "known_for_department": "Acting",
                "combined_credits": {"cast": self._get_mock_movies()}
            }
        return data

    def _get_gta_vi_special(self):
        return {
            "id": 1744462,
            "title": "Grand Theft Auto VI: An Extended Look",
            "name": "Grand Theft Auto VI: An Extended Look",
            "display_title": "Grand Theft Auto VI: An Extended Look",
            "tagline": "Welcome to Vice City. An exclusive extended cinematic showcase.",
            "overview": "See the premiere of an extended look at Grand Theft Auto VI, the next evolution in the groundbreaking Grand Theft Auto series.",
            "poster_path": "/xTZuh9ziUjIyHBWO9OvqNIPqVWe.jpg",
            "backdrop_path": "/po0uFYwWNByHQzHLCVJ6FetkN4M.jpg",
            "release_date": "2026-08-27",
            "first_air_date": "2026-08-27",
            "release_year": "2026",
            "runtime": 65,
            "vote_average": 9.6,
            "vote_count": 12500,
            "age_rating": "18+",
            "media_type": "movie",
            "genres": [{"id": 28, "name": "Action"}, {"id": 80, "name": "Crime"}, {"id": 12, "name": "Adventure"}],
            "credits": {
                "cast": [
                    {"id": 1001, "name": "Lucia", "character": "Protagonist", "profile_path": None},
                    {"id": 1002, "name": "Jason", "character": "Protagonist", "profile_path": None},
                    {"id": 1003, "name": "Sam Houser", "character": "Executive Producer", "profile_path": None}
                ]
            },
            "recommendations": {
                "results": [
                    {
                        "id": 157336,
                        "title": "Interstellar",
                        "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                        "vote_average": 8.4,
                        "release_date": "2014-11-05",
                        "age_rating": "PG-13",
                        "media_type": "movie"
                    }
                ]
            }
        }

    def _get_mock_movies(self):
        return [
            self._get_gta_vi_special(),
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
