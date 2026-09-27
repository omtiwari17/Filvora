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

    def test_franchise_sequels_seed_deduplication(self):
        """Verifies that rating two sequels in the same franchise (e.g. Across the Spider-Verse and Into the Spider-Verse)
        does not produce two duplicate franchise rails, but deduplicates to 1 franchise rail and picks a diverse second seed."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating
        from apps.accounts.models import UserProfile

        engine = RecommendationEngine()
        profile = UserProfile.objects.create(user=self.user, name='SpiderFan')

        # User rates 3 movies 5-star:
        # 1. Spider-Man: Across the Spider-Verse (part of Spider-Verse collection 573436)
        # 2. Spider-Man: Into the Spider-Verse (part of Spider-Verse collection 573436)
        # 3. Interstellar (standalone movie, no collection)
        UserRating.objects.create(user=self.user, profile=profile, tmdb_id=569094, media_type='movie', score=5)
        UserRating.objects.create(user=self.user, profile=profile, tmdb_id=324857, media_type='movie', score=5)
        UserRating.objects.create(user=self.user, profile=profile, tmdb_id=157336, media_type='movie', score=5)

        rails = engine.get_contextual_rails(self.user, profile=profile, max_rails=2)
        self.assertEqual(len(rails), 2)

        # Verify that we do not have two Spider-Verse rails
        titles = [r['title'] for r in rails]
        spider_verse_rails = [t for t in titles if 'Spider' in t]
        self.assertEqual(len(spider_verse_rails), 1, "Expected only 1 Spider-Man franchise rail, but got multiple!")

        # Verify the second rail is Interstellar (diverse favorite)
        self.assertIn('Interstellar', titles)

    def test_unwatched_sequel_prioritized_in_collection_recommendations(self):
        """Verifies that if a user rated/watched a movie in a collection, unstreamed sequels in that collection are prioritized."""
        from apps.core.recommendations import RecommendationEngine
        from apps.watch.models import UserRating
        from apps.accounts.models import UserProfile

        engine = RecommendationEngine()
        profile = UserProfile.objects.create(user=self.user, name='Collector')

        # User rated Into the Spider-Verse (324857) only
        UserRating.objects.create(user=self.user, profile=profile, tmdb_id=324857, media_type='movie', score=5)

        rails = engine.get_contextual_rails(self.user, profile=profile, max_rails=1)
        self.assertEqual(len(rails), 1)
        rail = rails[0]

        # The sequel (Across the Spider-Verse, id 569094) should be among the top items
        item_ids = [item.get('id') for item in rail['items']]
        self.assertIn(569094, item_ids, "Expected sequel (Across the Spider-Verse) to be recommended for Into the Spider-Verse!")

    def test_favicon_and_device_app_icons_exist_and_valid(self):
        """Verifies that all device OS icons, favicons, maskable icons, and OpenGraph preview files exist with valid non-empty byte sizes."""
        import os
        from django.conf import settings

        base_static = settings.STATICFILES_DIRS[0]
        icons_dir = os.path.join(base_static, 'icons')

        expected_files = [
            'favicon.ico',
            'favicon.svg',
            'favicon-16x16.png',
            'favicon-32x32.png',
            'favicon-48x48.png',
            'apple-touch-icon.png',
            'apple-touch-icon-120x120.png',
            'apple-touch-icon-152x152.png',
            'icon-192.png',
            'icon-192-maskable.png',
            'icon-512.png',
            'icon-512-maskable.png',
            'mstile-150x150.png',
            'mstile-310x310.png',
            'safari-pinned-tab.svg',
            'browserconfig.xml',
            'og-image.png'
        ]

        for fname in expected_files:
            fpath = os.path.join(icons_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Expected asset missing: {fpath}")
            size = os.path.getsize(fpath)
            self.assertGreater(size, 100, f"Asset file is unexpectedly small or empty: {fpath} ({size} bytes)")

        # Verify static/favicon.ico mirror exists
        self.assertTrue(os.path.exists(os.path.join(base_static, 'favicon.ico')))

    def test_root_favicon_and_manifest_redirects(self):
        """Verifies that requests to root /favicon.ico, /manifest.json, /browserconfig.xml, and /sw.js redirect correctly."""
        for endpoint, target_sub in [
            ('/favicon.ico', '/static/icons/favicon.ico'),
            ('/manifest.json', '/static/manifest.json'),
            ('/browserconfig.xml', '/static/icons/browserconfig.xml'),
            ('/sw.js', '/static/sw.js')
        ]:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 301, f"Expected 301 redirect for {endpoint}")
            self.assertIn(target_sub, response.url, f"Unexpected redirect target for {endpoint}: {response.url}")

    def test_base_template_meta_and_icons_integration(self):
        """Verifies that base.html includes all required multi-device favicon, apple-touch-icon, Windows tile, OG, and install modal tags."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Favicons
        self.assertIn('rel="icon" type="image/svg+xml" href="/static/icons/favicon.svg"', content)
        self.assertIn('rel="icon" type="image/x-icon" href="/static/icons/favicon.ico"', content)
        self.assertIn('rel="icon" type="image/png" sizes="32x32"', content)
        self.assertIn('rel="icon" type="image/png" sizes="16x16"', content)

        # Apple Touch Icons
        self.assertIn('rel="apple-touch-icon" sizes="180x180"', content)
        self.assertIn('rel="mask-icon" href="/static/icons/safari-pinned-tab.svg"', content)
        self.assertIn('name="apple-mobile-web-app-capable" content="yes"', content)

        # Windows Tiles
        self.assertIn('name="msapplication-TileImage" content="/static/icons/mstile-150x150.png"', content)
        self.assertIn('name="msapplication-config" content="/static/icons/browserconfig.xml"', content)

        # OpenGraph
        self.assertIn('property="og:image" content="/static/icons/og-image.png"', content)
        self.assertIn('name="twitter:image" content="/static/icons/og-image.png"', content)

        # Manifest
        self.assertIn('rel="manifest" href="/static/manifest.json"', content)

        # Install App Modal
        self.assertIn('id="install-app-modal"', content)
        self.assertIn('triggerPwaInstall', content)
        self.assertIn('openInstallModal', content)

    def test_manifest_json_structure_and_local_icons(self):
        """Verifies that static/manifest.json is valid JSON with proper local multi-OS icon references and maskable assets."""
        import json, os
        from django.conf import settings

        manifest_path = os.path.join(settings.STATICFILES_DIRS[0], 'manifest.json')
        self.assertTrue(os.path.exists(manifest_path))

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get('name'), 'Filvora — Ultimate Cinematic Streaming')
        self.assertEqual(manifest.get('short_name'), 'Filvora')
        self.assertEqual(manifest.get('display'), 'standalone')
        self.assertEqual(manifest.get('background_color'), '#030712')

        icons = manifest.get('icons', [])
        self.assertGreaterEqual(len(icons), 4)

        icon_srcs = [i['src'] for i in icons]
        self.assertIn('/static/icons/icon-192.png', icon_srcs)
        self.assertIn('/static/icons/icon-512.png', icon_srcs)
        self.assertIn('/static/icons/icon-192-maskable.png', icon_srcs)
        self.assertIn('/static/icons/icon-512-maskable.png', icon_srcs)

        # Verify maskable purpose is declared
        purposes = [i.get('purpose') for i in icons]
        self.assertIn('maskable', purposes)


class AdminDashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(username='regular', password='password123')
        self.staff_user = User.objects.create_user(username='staffadmin', password='password123', is_staff=True)
        self.superuser = User.objects.create_superuser(username='superadmin', password='password123', email='admin@filvora.com')

    def test_admin_dashboard_anonymous_redirect(self):
        response = self.client.get('/admin/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_admin_dashboard_non_staff_redirect(self):
        self.client.login(username='regular', password='password123')
        response = self.client.get('/admin/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_staff_access_success(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.get('/admin/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('system', response.context)
        self.assertIn('users', response.context)
        self.assertIn('streaming', response.context)
        self.assertIn('ratings', response.context)
        self.assertIn('library', response.context)
        self.assertIn('models', response.context)
        content = response.content.decode('utf-8')
        self.assertIn('Admin & Developer Dashboard', content)
        self.assertIn('Purge Cache', content)
        self.assertIn('Test TMDB Ping', content)

    def test_admin_purge_cache_endpoint(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.post('/admin/dashboard/purge-cache/', HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Cache Purged', response.content.decode('utf-8'))

    def test_admin_ping_tmdb_endpoint(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.get('/admin/dashboard/ping-tmdb/', HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)

    def test_admin_check_db_endpoint(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.post('/admin/dashboard/check-db/', HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('PRAGMA check', response.content.decode('utf-8'))

    def test_admin_reset_breaker_endpoint(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.post('/admin/dashboard/reset-breaker/', HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Circuit Breaker Reset', response.content.decode('utf-8'))

    def test_admin_quick_inspect_endpoints(self):
        self.client.login(username='staffadmin', password='password123')
        # inspect by username
        resp1 = self.client.get('/admin/dashboard/inspect/?q=regular')
        self.assertEqual(resp1.status_code, 200)
        self.assertIn('regular', resp1.content.decode('utf-8'))

        # inspect by tmdb id
        resp2 = self.client.get('/admin/dashboard/inspect/?q=157336')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('TMDB ID #157336', resp2.content.decode('utf-8'))

    def test_admin_models_registered_in_django_admin(self):
        from django.contrib import admin
        from apps.accounts.models import UserProfile
        from apps.library.models import LibraryItem, CustomCollection, SceneBookmark, FavoritePerson
        from apps.playback.models import PlaybackServerPreference
        from apps.watch.models import WatchProgress, UserRating

        self.assertIn(UserProfile, admin.site._registry)
        self.assertIn(LibraryItem, admin.site._registry)
        self.assertIn(CustomCollection, admin.site._registry)
        self.assertIn(SceneBookmark, admin.site._registry)
        self.assertIn(FavoritePerson, admin.site._registry)
        self.assertIn(PlaybackServerPreference, admin.site._registry)
        self.assertIn(WatchProgress, admin.site._registry)
        self.assertIn(UserRating, admin.site._registry)










