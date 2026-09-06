from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.watch.models import WatchProgress
from apps.library.models import LibraryItem

class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_home_view_anonymous(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('trending_movies', response.context)
        self.assertIn('popular_movies', response.context)
        self.assertIn('upcoming_releases', response.context)
        self.assertEqual(len(response.context['continue_watching']), 0)

    def test_home_view_authenticated_with_continue_watching(self):
        self.client.login(username='testuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=120,
            duration_seconds=7200,
            completed=False
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['continue_watching']), 1)
        self.assertEqual(response.context['continue_watching'][0]['tmdb_id'], 157336)
        self.assertIsNotNone(response.context['because_title'])

    def test_home_view_with_my_list_preview(self):
        self.client.login(username='testuser', password='password123')
        LibraryItem.objects.create(user=self.user, tmdb_id=157336, media_type='movie')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['my_list_preview']), 1)
        self.assertIn('scifi_movies', response.context)
        self.assertIn('recommended_for_you', response.context)

    def test_recommendation_engine_affinity(self):
        from apps.core.recommendations import RecommendationEngine
        engine = RecommendationEngine()
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=3600,
            duration_seconds=7200,
            completed=True
        )
        recs = engine.get_personalized_recommendations(self.user)
        self.assertIsNotNone(recs)
        self.assertGreater(len(recs), 0)

        because = engine.get_because_you_watched(self.user)
        self.assertIsNotNone(because)
        self.assertEqual(because['title'], 'Interstellar')

    def test_pwa_assets_and_manifest(self):
        import os, json
        from django.conf import settings
        manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['short_name'], 'Filvora')
            self.assertEqual(data['display'], 'standalone')

        sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
        self.assertTrue(os.path.exists(sw_path))

        # Check manifest linked in base HTML
        response = self.client.get('/')
        self.assertIn('manifest.json', response.content.decode('utf-8'))

    def test_csrf_failure_view_browser(self):
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/accounts/login/', {'username': 'test'})
        request.META['HTTP_REFERER'] = '/accounts/login/'
        response = csrf_failure(request, reason="CSRF token from POST incorrect.")
        self.assertEqual(response.status_code, 403)
        self.assertIn('Security Token Refreshed', response.content.decode('utf-8'))
        self.assertIn('csrf-countdown', response.content.decode('utf-8'))
        # Ensure fresh CSRF cookie was issued
        self.assertIn('csrftoken', response.cookies)

    def test_csrf_failure_view_htmx(self):
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/library/toggle/', HTTP_HX_REQUEST='true')
        response = csrf_failure(request, reason="CSRF token from POST incorrect.")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['HX-Refresh'], 'true')
        self.assertIn('csrftoken', response.cookies)

    def test_csrf_failure_view_json(self):
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        import json
        factory = RequestFactory()
        request = factory.post('/library/bookmark/add/', HTTP_ACCEPT='application/json')
        response = csrf_failure(request, reason="CSRF token from POST incorrect.")
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'error')
        self.assertIn('csrftoken', response.cookies)

    def test_csrf_settings_configuration(self):
        from django.conf import settings
        self.assertEqual(settings.CSRF_FAILURE_VIEW, 'apps.core.views.csrf_failure')
        self.assertFalse(settings.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
        self.assertIn('http://localhost:8000', settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn('http://localhost', settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn('http://127.0.0.1:8000', settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn('http://127.0.0.1', settings.CSRF_TRUSTED_ORIGINS)




