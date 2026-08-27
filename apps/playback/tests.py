import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.watch.models import WatchProgress
from apps.playback.models import PlaybackServerPreference
from apps.playback.providers import registry, get_provider, PlaybackProvider

class PlaybackTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='playbackuser', password='password123')

    def test_watch_requires_login(self):
        response = self.client.get('/watch/movie/157336/')
        self.assertEqual(response.status_code, 302)

    def test_watch_movie_authenticated(self):
        self.client.login(username='playbackuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=120,
            duration_seconds=7200
        )
        response = self.client.get('/watch/movie/157336/?server=vidlink')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resume_position'], 120.0)
        self.assertEqual(response.context['current_server'], 'vidlink')
        self.assertIn('video_url', response.context)
        self.assertIsNotNone(response.context['next_provider'])

    def test_watch_series_episode(self):
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/tv/1399/1/2/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['season'], 1)
        self.assertEqual(response.context['episode'], 2)
        self.assertIsNotNone(response.context['next_episode'])
        self.assertEqual(response.context['next_episode']['episode'], 3)

    def test_provider_registry_priority_and_fallback(self):
        ordered = registry.get_ordered_providers()
        self.assertGreater(len(ordered), 1)
        self.assertEqual(ordered[0].id, 'vidlink')
        self.assertEqual(ordered[1].id, 'autoembed')

        # Test next provider fallback calculation
        next_after_vidlink = registry.get_next_provider('vidlink')
        self.assertEqual(next_after_vidlink.id, 'autoembed')

        # Test custom preference ordering
        custom_ordered = registry.get_ordered_providers(preferred_id='autoembed')
        self.assertEqual(custom_ordered[0].id, 'autoembed')

    def test_sticky_server_preference(self):
        self.client.login(username='playbackuser', password='password123')
        # Save a preference for autoembed
        PlaybackServerPreference.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            provider_id='autoembed'
        )

        # Loading without server param should automatically pick autoembed
        response = self.client.get('/watch/movie/157336/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_server'], 'autoembed')

    def test_report_server_success_endpoint(self):
        self.client.login(username='playbackuser', password='password123')
        payload = {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'provider_id': '2embed'
        }
        response = self.client.post(
            '/watch/server-success/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

        pref = PlaybackServerPreference.objects.get(user=self.user, tmdb_id=157336)
        self.assertEqual(pref.provider_id, '2embed')

    def test_diagnostics_endpoint(self):
        self.client.login(username='playbackuser', password='password123')
        # Test HTML view
        res_html = self.client.get('/watch/diagnostics/')
        self.assertEqual(res_html.status_code, 200)
        self.assertIn('diagnostics', res_html.context)

        # Test JSON view
        res_json = self.client.get('/watch/diagnostics/?format=json')
        self.assertEqual(res_json.status_code, 200)
        self.assertIn('providers', res_json.json())

    def test_player_resume_formatting_and_episode_navigation(self):
        self.client.login(username='playbackuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=1399,
            media_type='tv',
            season=2,
            episode=3,
            position_seconds=2832,  # 47m 12s
            duration_seconds=3600
        )
        response = self.client.get('/watch/tv/1399/2/3/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resume_formatted'], '47:12')
        self.assertIsNotNone(response.context['previous_episode'])
        self.assertEqual(response.context['previous_episode']['episode'], 2)
        self.assertIsNotNone(response.context['next_episode'])
        self.assertEqual(response.context['next_episode']['episode'], 4)
