from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.library.models import LibraryItem

class CatalogViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cataloguser', password='password123')

    def test_movie_browse(self):
        response = self.client.get('/movies/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('movies', response.context)

    def test_movie_detail(self):
        response = self.client.get('/movies/157336/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('movie', response.context)
        self.assertEqual(response.context['movie']['id'], 157336)

    def test_series_browse(self):
        response = self.client.get('/series/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('series_list', response.context)

    def test_series_detail(self):
        response = self.client.get('/series/1399/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('series', response.context)
        self.assertEqual(response.context['series']['id'], 1399)

    def test_season_episodes(self):
        response = self.client.get('/series/1399/season/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('episodes', response.context)

    def test_search_results(self):
        response = self.client.get('/search/?q=Interstellar')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)

    def test_search_suggest(self):
        response = self.client.get('/search/suggest/?q=Dune')
        self.assertEqual(response.status_code, 200)
        self.assertIn('categorized', response.context)

    def test_discover_view(self):
        response = self.client.get('/discover/?type=movie&genre=28&rating=7.0')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertIn('genres', response.context)
        self.assertEqual(response.context['media_type'], 'movie')

    def test_surprise_me_redirect(self):
        response = self.client.get('/surprise-me/?type=movie')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/movies/') or response.url.startswith('/series/'))

    def test_genres_view(self):
        response = self.client.get('/genres/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('genres', response.context)

    def test_discover_with_language_and_certification(self):
        response = self.client.get('/discover/?type=movie&language=ja&certification=PG-13')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_language'], 'ja')
        self.assertEqual(response.context['selected_certification'], 'PG-13')

    def test_kids_profile_discover_enforcement(self):
        self.client.login(username='cataloguser', password='password123')
        from apps.accounts.models import UserProfile
        kids_profile = UserProfile.objects.create(user=self.user, name='Kids', is_kids=True)
        session = self.client.session
        session['active_profile_id'] = kids_profile.id
        session.save()

        response = self.client.get('/discover/?type=movie')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_kids_mode'])

