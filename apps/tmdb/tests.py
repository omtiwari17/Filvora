from django.test import TestCase
from apps.tmdb.client import TMDBClient

class TMDBTestCase(TestCase):
    def setUp(self):
        self.client = TMDBClient()

    def test_mock_movies_fallback(self):
        movies = self.client._get_mock_movies()
        self.assertGreater(len(movies), 0)
        self.assertEqual(movies[0]['title'], 'Interstellar')

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
