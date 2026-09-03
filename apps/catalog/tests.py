from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.library.models import LibraryItem

class CatalogViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cataloguser', password='password123')

    def test_movie_browse(self):
        response = self.client.get('/movies/?category=top_rated&page=2')
        self.assertEqual(response.status_code, 200)
        self.assertIn('movies', response.context)
        self.assertIn('genres', response.context)
        self.assertIn('pagination', response.context)
        self.assertEqual(response.context['pagination']['current_page'], 2)

    def test_movie_detail(self):
        response = self.client.get('/movies/157336/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('movie', response.context)
        self.assertEqual(response.context['movie']['id'], 157336)

    def test_series_browse(self):
        response = self.client.get('/series/?category=trending&page=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('series_list', response.context)
        self.assertIn('genres', response.context)
        self.assertIn('pagination', response.context)

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

    def test_search_with_age_rating(self):
        response = self.client.get('/search/?q=Interstellar rating:PG-13')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['selected_rating'], 'PG-13')

    def test_search_standalone_rating_query(self):
        response = self.client.get('/search/?q=PG-13')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['selected_rating'], 'PG-13')

        response2 = self.client.get('/search/?q=t=R')
        self.assertEqual(response2.status_code, 200)
        self.assertIn('results', response2.context)
        self.assertEqual(response2.context['selected_rating'], 'R')

    def test_search_suggest(self):
        response = self.client.get('/search/suggest/?q=Dune')
        self.assertEqual(response.status_code, 200)
        self.assertIn('categorized', response.context)

    def test_gta_vi_search_and_detail(self):
        response = self.client.get('/search/?q=GTA+VI')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertTrue(any(r.get('id') in [1744462, 1222222] for r in response.context['results']))

        detail_resp = self.client.get('/movies/1744462/')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.context['movie']['title'], "Grand Theft Auto VI: An Extended Look")

    def test_discover_view(self):
        response = self.client.get('/discover/?type=movie&genre=28&rating=7.0&page=2')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertIn('genres', response.context)
        self.assertIn('pagination', response.context)
        self.assertEqual(response.context['pagination']['current_page'], 2)
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

    def test_person_detail_view(self):
        response = self.client.get('/person/10297/') # Matthew McConaughey / actor mock
        self.assertEqual(response.status_code, 200)
        self.assertIn('person', response.context)
        self.assertIn('credits', response.context)

    def test_trailer_api(self):
        response = self.client.get('/trailer/movie/550/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('trailer_key', data)
        self.assertEqual(data['tmdb_id'], 550)
        self.assertEqual(data['media_type'], 'movie')

    def test_movie_detail_trailer_context(self):
        response = self.client.get('/movies/550/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('trailer_key', response.context)

    def test_franchise_collection_context(self):
        response = self.client.get('/movies/245891/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('collection', response.context)
        col = response.context['collection']
        if col:
            self.assertIn('parts', col)
            self.assertTrue(len(col['parts']) >= 1)
            has_current = any(p.get('is_current') for p in col['parts'])
            self.assertTrue(has_current)


