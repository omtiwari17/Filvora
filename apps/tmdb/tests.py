from django.test import TestCase
from apps.tmdb.client import TMDBClient

class TMDBTestCase(TestCase):
    def setUp(self):
        self.client = TMDBClient()

    def test_mock_movies_fallback(self):
        movies = self.client._get_mock_movies()
        self.assertGreater(len(movies), 0)
        self.assertTrue(any(m['title'] == 'Interstellar' for m in movies))

    def test_mock_series_fallback(self):
        series = self.client._get_mock_series()
        self.assertGreater(len(series), 0)
        self.assertEqual(series[0]['name'], 'Game of Thrones')

    def test_attach_age_rating_movie(self):
        item = {'title': 'Kids Animated Movie', 'genre_ids': [16, 10751]}
        rated = self.client._attach_age_rating(item, 'movie')
        self.assertEqual(rated['age_rating'], 'PG')

        item_r = {'title': 'Horror Movie', 'genre_ids': [27]}
        rated_r = self.client._attach_age_rating(item_r, 'movie')
        self.assertEqual(rated_r['age_rating'], 'R')

    def test_attach_age_rating_tv(self):
        item = {'name': 'Adult Drama Series', 'genre_ids': [18, 80]}
        rated = self.client._attach_age_rating(item, 'tv')
        self.assertEqual(rated['age_rating'], 'TV-MA')

    def test_get_movie_details(self):
        movie = self.client.get_movie_details(157336)
        self.assertIsNotNone(movie)
        self.assertIn('title', movie)
        self.assertIn('age_rating', movie)
        self.assertIn('theatrical_release_display', movie)
        self.assertIn('ott_release_display', movie)

    def test_movie_release_date_and_ott_extraction(self):
        sample_payload = {
            'id': 1081003,
            'title': 'Supergirl',
            'release_date': '2026-06-24',
            'release_dates': {
                'results': [
                    {
                        'iso_3166_1': 'US',
                        'release_dates': [
                            {'type': 1, 'release_date': '2026-06-22T00:00:00.000Z', 'note': 'Premiere'},
                            {'type': 3, 'release_date': '2026-06-26T00:00:00.000Z', 'note': ''},
                            {'type': 4, 'release_date': '2026-07-28T00:00:00.000Z', 'note': ''},
                            {'type': 4, 'release_date': '2026-09-10T00:00:00.000Z', 'note': 'HBO Max'},
                        ]
                    }
                ]
            },
            'watch/providers': {
                'results': {
                    'US': {'flatrate': [{'provider_name': 'HBO Max'}]}
                }
            }
        }
        rel_info = self.client._extract_movie_release_info(sample_payload)
        self.assertEqual(rel_info['theatrical_release_date'], '2026-06-26')
        self.assertEqual(rel_info['theatrical_release_display'], 'Jun 26, 2026')
        self.assertEqual(rel_info['digital_release_date'], '2026-07-28')
        self.assertEqual(rel_info['ott_release_date'], '2026-09-10')
        self.assertEqual(rel_info['ott_release_display'], 'Sep 10, 2026')
        self.assertEqual(rel_info['ott_platform'], 'HBO Max')
        self.assertIn('HBO Max', rel_info['streaming_providers'])

    def test_tv_release_info_extraction(self):
        sample_payload = {
            'id': 100088,
            'name': 'The Last of Us',
            'first_air_date': '2023-01-15',
            'last_air_date': '2025-05-25',
            'status': 'Returning Series',
            'networks': [{'name': 'HBO'}],
            'watch/providers': {
                'results': {
                    'US': {'flatrate': [{'provider_name': 'HBO Max'}]}
                }
            }
        }
        tv_info = self.client._extract_tv_release_info(sample_payload)
        self.assertEqual(tv_info['first_air_display'], 'Jan 15, 2023')
        self.assertEqual(tv_info['last_air_display'], 'May 25, 2025')
        self.assertEqual(tv_info['primary_platform'], 'HBO Max')
        self.assertIn('HBO', tv_info['networks_list'])

    def test_search_categorized(self):
        res = self.client.search_categorized('Batman')
        self.assertIn('movies', res)
        self.assertIn('series', res)
        self.assertIn('people', res)

    def test_get_genres_list(self):
        genres = self.client.get_genres_list()
        self.assertGreater(len(genres), 5)
        self.assertEqual(genres[0]['id'], 28)

    def test_discover_content(self):
        results = self.client.discover_content(media_type='movie', mood='adrenaline')
        self.assertGreater(len(results), 0)

    def test_get_surprise_title(self):
        pick = self.client.get_surprise_title(media_type='movie')
        self.assertIsNotNone(pick)
        self.assertIn('id', pick)

    def test_discover_content_with_filters(self):
        results = self.client.discover_content(
            media_type='movie',
            language='ja',
            certification='PG-13',
            kids_only=True
        )
        self.assertGreater(len(results), 0)

    def test_get_content_rating_and_cache(self):
        # Horror movie (genre 27) -> R rating
        item = {'id': 999999, 'title': 'Horror Night', 'genre_ids': [27]}
        rated = self.client._attach_age_rating(item, 'movie')
        self.assertEqual(rated['age_rating'], 'R')
        self.assertEqual(self.client._RATING_CACHE.get('movie:999999'), 'R')

    def test_get_genres_list_tv_and_zero_emojis(self):
        movie_genres = self.client.get_genres_list('movie')
        tv_genres = self.client.get_genres_list('tv')
        self.assertEqual(movie_genres[0]['id'], 28)
        self.assertEqual(tv_genres[0]['id'], 10759)
        self.assertEqual(tv_genres[0]['name'], 'Action & Adventure')
        
        # Verify strict zero emoji rule (no emojis in genre names or dictionaries)
        import re
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        for g in movie_genres + tv_genres:
            self.assertFalse(bool(emoji_pattern.search(g['name'])))
            self.assertNotIn('icon', g)

    def test_genre_resolution_cross_media(self):
        # Movie action (28) -> TV Action & Adventure (10759)
        self.assertEqual(self.client._resolve_genre_for_media_type(28, 'tv'), 10759)
        # Movie scifi (878) -> TV Sci-Fi & Fantasy (10765)
        self.assertEqual(self.client._resolve_genre_for_media_type(878, 'tv'), 10765)
        # TV Action (10759) -> Movie Action (28)
        self.assertEqual(self.client._resolve_genre_for_media_type(10759, 'movie'), 28)

    def test_discover_content_audience_filters(self):
        live_movies = self.client.discover_content(media_type='movie', genre_id=35, audience='live_action')
        self.assertGreater(len(live_movies), 0)

        kids_movies = self.client.discover_content(media_type='movie', genre_id=35, audience='kids_family')
        self.assertGreater(len(kids_movies), 0)

    def test_tv_certification_conversion(self):
        # Passing R to TV discover converts to TV-MA without error
        tv_results = self.client.discover_content(media_type='tv', certification='R')
        self.assertGreater(len(tv_results), 0)

    def test_get_tv_details(self):
        tv = self.client.get_tv_details(1399) # Game of Thrones
        self.assertIsNotNone(tv)
        self.assertIn('name', tv)
        self.assertIn('age_rating', tv)

    def test_get_series_season(self):
        season_data = self.client.get_tv_season(1399, 1)
        self.assertIsNotNone(season_data)
        self.assertIn('episodes', season_data)
        self.assertGreater(len(season_data['episodes']), 0)

    def test_search_multi_empty(self):
        results = self.client.search_multi('')
        self.assertEqual(results, [])

    def test_discover_tv_maps_primary_release_date_sort_to_first_air_date(self):
        from unittest.mock import patch
        with patch.object(self.client, '_fetch_paginated_24', return_value=[]) as mock_fetch:
            self.client.discover_content(media_type='tv', sort_by='primary_release_date.asc')
            mock_fetch.assert_called_once()
            endpoint, params = mock_fetch.call_args[0]
            self.assertEqual(endpoint, '/discover/tv')
            self.assertEqual(params['sort_by'], 'first_air_date.asc')

    def test_canonical_movie_alias_resolution_and_search_dedup(self):
        """Verifies TMDB client resolves re-release editions, links parents, and preserves both in search."""
        from unittest.mock import patch
        # 1. Stale stub 1824694 resolves to live entry 1824935
        self.assertEqual(self.client.resolve_movie_alias(1824694), 1824935)
        self.assertEqual(self.client.resolve_movie_alias(1824935), 1824935)

        # 2. find_parent_movie generic detection for edition titles
        with patch.object(self.client, '_fetch', return_value={'results': [{'id': 299534, 'title': 'Avengers: Endgame'}]}):
            parent = self.client.find_parent_movie('Avengers Endgame: Encore')
            self.assertIsNotNone(parent)
            self.assertEqual(parent['id'], 299534)

        # 3. Search multi preserves both edition (1824935) and parent (299534)
        mock_search_results = {
            'results': [
                {'id': 1824694, 'media_type': 'movie', 'title': 'Avengers Endgame: Encore', 'poster_path': '/encore.jpg', 'release_date': '2026-09-24'},
                {'id': 299534, 'media_type': 'movie', 'title': 'Avengers: Endgame', 'poster_path': '/endgame.jpg', 'release_date': '2019-04-24'},
            ],
            'total_pages': 1,
            'total_results': 2
        }
        with patch.object(self.client, '_fetch', return_value=mock_search_results):
            data = self.client.search_multi_paginated('avengers endgame encore')
            ids = [r['id'] for r in data['results']]
            self.assertIn(1824935, ids)
            self.assertIn(299534, ids)
            self.assertEqual(len(ids), 2)





