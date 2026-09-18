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

    def test_404_handler(self):
        response = self.client.get('/definitely-non-existent-page-xyz-123/')
        self.assertEqual(response.status_code, 404)

    def test_kids_mode_homepage_content_filtering(self):
        from apps.accounts.models import UserProfile
        kids_profile = UserProfile.objects.create(user=self.user, name='Kids Profile', is_kids=True)
        self.client.login(username='testuser', password='password123')
        session = self.client.session
        session['active_profile_id'] = kids_profile.id
        session.save()

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['active_profile'])
        self.assertTrue(response.context['active_profile'].is_kids)


    def test_recommendations_with_empty_history(self):
        from apps.core.recommendations import RecommendationEngine
        engine = RecommendationEngine()
        # User has 0 watch progress
        recs = engine.get_personalized_recommendations(self.user)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)
        because = engine.get_because_you_watched(self.user)
        self.assertIsNone(because)

    def test_home_view_offline_empty_state(self):
        """Verifies cinematic offline empty state billboard renders when catalog is empty or offline."""
        from unittest.mock import patch
        with patch('apps.tmdb.client.TMDBClient.get_trending_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_popular_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_popular_series', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_top_rated_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_top_rated_series', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_action_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_scifi_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_animation_movies', return_value=[]), \
             patch('apps.tmdb.client.TMDBClient.get_movies_catalog', return_value=[]):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['is_empty_catalog'])
            html = response.content.decode('utf-8')
            self.assertIn('offline-hero-billboard', html)
            self.assertIn("You're Currently Offline", html)
            self.assertIn('Check Connection & Retry', html)
            self.assertIn('/library/', html)

    def test_offline_vendor_assets_and_critical_css(self):
        """Verifies offline vendor assets exist locally and critical inline CSS safeguards against FOUC & SVG explosion."""
        import os
        from django.conf import settings
        tailwind_vendor = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'tailwind.min.js')
        htmx_vendor = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'htmx.min.js')
        self.assertTrue(os.path.exists(tailwind_vendor), "static/vendor/tailwind.min.js must exist for offline use")
        self.assertTrue(os.path.exists(htmx_vendor), "static/vendor/htmx.min.js must exist for offline use")

        response = self.client.get('/')
        html = response.content.decode('utf-8')
        # Critical inline CSS safeguards
        self.assertIn('background-color: #030712', html)
        self.assertIn('svg.w-4', html)
        self.assertIn('vendor/tailwind.min.js', html)
        self.assertIn('vendor/htmx.min.js', html)

    def test_network_status_indicator_present(self):
        """Verifies ambient floating network status HUD indicator is rendered in base template."""
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        self.assertIn('id="network-status-indicator"', html)
        self.assertIn('id="network-status-badge"', html)

    def test_unstreamed_5_star_rating_attribution(self):
        """Verifies that rating a movie 5 stars without streaming it attributes as 'Because You Loved' and NEVER 'Because You Watched'."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating
        from apps.accounts.models import UserProfile

        engine = RecommendationEngine()
        profile = UserProfile.objects.create(user=self.user, name='Main Profile')

        # User rated movie 5 stars but never streamed it on Filvora
        UserRating.objects.create(
            user=self.user,
            profile=profile,
            tmdb_id=157336,
            media_type='movie',
            score=5
        )

        attr = engine.get_seed_attribution(self.user, profile, 157336, 'movie')
        self.assertEqual(attr, "Because You Loved")

        rail = engine.get_because_you_watched(self.user, profile=profile)
        self.assertIsNotNone(rail)
        self.assertEqual(rail['reason_prefix'], "Because You Loved")
        self.assertNotEqual(rail['reason_prefix'], "Because You Watched")

        # Verify on HomeView
        self.client.login(username='testuser', password='password123')
        session = self.client.session
        session['active_profile_id'] = profile.id
        session.save()

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Because You Loved', html)
        self.assertNotIn('Because You Watched <span class="text-brand-500">Interstellar</span>', html)

    def test_unstreamed_4_star_rating_attribution(self):
        """Verifies that rating a movie 4 stars without streaming it attributes as 'Because You Liked'."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating

        engine = RecommendationEngine()
        UserRating.objects.create(
            user=self.user,
            tmdb_id=550,
            media_type='movie',
            score=4
        )
        attr = engine.get_seed_attribution(self.user, None, 550, 'movie')
        self.assertEqual(attr, "Because You Liked")

    def test_streamed_title_attribution(self):
        """Verifies that streaming a movie on Filvora without rating it attributes as 'Because You Watched'."""
        from apps.core.recommendations import RecommendationEngine
        engine = RecommendationEngine()
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=550,
            media_type='movie',
            position_seconds=120,
            duration_seconds=7200,
            completed=False
        )
        attr = engine.get_seed_attribution(self.user, None, 550, 'movie')
        self.assertEqual(attr, "Because You Watched")

    def test_multi_seed_contextual_rails_diversity(self):
        """Verifies that rating multiple movies yields multiple distinct contextual rails with no duplicates."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating

        engine = RecommendationEngine()
        # Rate two different movies
        UserRating.objects.create(user=self.user, tmdb_id=157336, media_type='movie', score=5)
        UserRating.objects.create(user=self.user, tmdb_id=550, media_type='movie', score=4)

        rails = engine.get_contextual_rails(self.user, max_rails=2)
        self.assertGreaterEqual(len(rails), 1)
        # Ensure seed IDs are distinct
        seed_ids = [r['tmdb_id'] for r in rails]
        self.assertEqual(len(seed_ids), len(set(seed_ids)))

    def test_personalized_recommendations_exclusions(self):
        """Verifies that movies already rated or watched are excluded from recommended_for_you."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating

        engine = RecommendationEngine()
        # User rated Interstellar (157336)
        UserRating.objects.create(user=self.user, tmdb_id=157336, media_type='movie', score=5)
        recs = engine.get_personalized_recommendations(self.user)
        self.assertIsNotNone(recs)
        rec_ids = [m.get('id') for m in recs]
        # Seed itself must be excluded from recommendations
        self.assertNotIn(157336, rec_ids)

    def test_profile_isolation_in_recommendations(self):
        """Verifies that ratings in Profile 1 do not leak recommendations into Profile 2."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating
        from apps.accounts.models import UserProfile

        engine = RecommendationEngine()
        p1 = UserProfile.objects.create(user=self.user, name='Profile 1')
        p2 = UserProfile.objects.create(user=self.user, name='Profile 2')

        UserRating.objects.create(user=self.user, profile=p1, tmdb_id=157336, media_type='movie', score=5)

        # Profile 1 should have contextual rails
        rails_p1 = engine.get_contextual_rails(self.user, profile=p1)
        self.assertGreater(len(rails_p1), 0)

        # Profile 2 has 0 ratings and 0 watch progress, should have empty contextual rails
        rails_p2 = engine.get_contextual_rails(self.user, profile=p2)
        self.assertEqual(len(rails_p2), 0)

    def test_recommendations_view_authenticated(self):
        """Verifies /recommendations/ dedicated page renders 200 OK with personalized payload for authenticated user."""
        from apps.watch.models import UserRating
        UserRating.objects.create(user=self.user, tmdb_id=157336, media_type='movie', score=5)
        self.client.login(username='testuser', password='password123')

        response = self.client.get('/recommendations/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('top_picks', response.context)
        self.assertIn('ratings_rails', response.context)
        self.assertIn('stats', response.context)
        self.assertEqual(response.context['media_filter'], 'all')
        html = response.content.decode('utf-8')
        self.assertIn('Personalized Recommendations', html)
        self.assertIn('Because You Loved', html)

    def test_recommendations_view_anonymous(self):
        """Verifies /recommendations/ dedicated page renders 200 OK with general fallback content for guest visitors."""
        response = self.client.get('/recommendations/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('top_picks', response.context)
        html = response.content.decode('utf-8')
        self.assertIn('Personalized Recommendations', html)

    def test_recommendations_view_type_filters(self):
        """Verifies /recommendations/?type=movie and /recommendations/?type=tv apply type filters."""
        self.client.login(username='testuser', password='password123')

        resp_movie = self.client.get('/recommendations/?type=movie')
        self.assertEqual(resp_movie.status_code, 200)
        self.assertEqual(resp_movie.context['media_filter'], 'movie')

        resp_tv = self.client.get('/recommendations/?type=tv')
        self.assertEqual(resp_tv.status_code, 200)
        self.assertEqual(resp_tv.context['media_filter'], 'tv')

    def test_dedicated_recommendations_ratings_and_history_partitioning(self):
        """Verifies that get_dedicated_recommendations cleanly separates ratings-driven picks from history-driven picks."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating

        engine = RecommendationEngine()
        # Seed 1: Rated 5 stars (never streamed)
        UserRating.objects.create(user=self.user, tmdb_id=157336, media_type='movie', score=5)
        # Seed 2: Streamed on Filvora (never rated)
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=550,
            media_type='movie',
            position_seconds=600,
            duration_seconds=7200,
            completed=True
        )

        data = engine.get_dedicated_recommendations(self.user, media_filter='all')
        self.assertTrue(data['has_signals'])
        self.assertEqual(data['stats']['total_rated'], 1)
        self.assertEqual(data['stats']['total_streamed'], 1)

        # Ratings rails must contain the 5-star rated title with 'Because You Loved'
        self.assertGreaterEqual(len(data['ratings_rails']), 1)
        self.assertEqual(data['ratings_rails'][0]['reason_prefix'], "Because You Loved")
        self.assertEqual(data['ratings_rails'][0]['title'], "Interstellar")

        # History rails must contain the streamed title with 'Because You Watched'
        self.assertGreaterEqual(len(data['history_rails']), 1)
        self.assertEqual(data['history_rails'][0]['reason_prefix'], "Because You Watched")








