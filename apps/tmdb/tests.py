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
        # Call Me by Your Name (id: 398818)
        item = {'id': 398818, 'title': 'Call Me by Your Name', 'genre_ids': [10749, 18]}
        rated = self.client._attach_age_rating(item, 'movie')
        self.assertEqual(rated['age_rating'], 'R')
        self.assertEqual(self.client._RATING_CACHE.get('movie:398818'), 'R')

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


