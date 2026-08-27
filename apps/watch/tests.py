import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.watch.models import WatchProgress

class WatchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='watchuser', password='password123')

    def test_save_progress_json(self):
        self.client.login(username='watchuser', password='password123')
        payload = {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'position': 300,
            'duration': 6000
        }
        response = self.client.post(
            '/progress/save/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['completed'], False)
        self.assertEqual(data['progress_percentage'], 5.0)

        progress = WatchProgress.objects.get(user=self.user, tmdb_id=157336)
        self.assertEqual(progress.position_seconds, 300)
        self.assertEqual(progress.duration_seconds, 6000)

    def test_save_progress_completed_threshold(self):
        self.client.login(username='watchuser', password='password123')
        payload = {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'position': 5800,
            'duration': 6000
        }
        response = self.client.post(
            '/progress/save/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['completed'])

    def test_remove_progress_htmx(self):
        self.client.login(username='watchuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=300,
            duration_seconds=6000
        )
        response = self.client.post(
            '/progress/remove/',
            {'tmdb_id': 157336, 'media_type': 'movie'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), '')
        self.assertFalse(WatchProgress.objects.filter(user=self.user, tmdb_id=157336).exists())

    def test_history_view(self):
        self.client.login(username='watchuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=1200,
            duration_seconds=7200
        )
        response = self.client.get('/history/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('grouped_history', response.context)
        self.assertEqual(response.context['total_items'], 1)

    def test_clear_history(self):
        self.client.login(username='watchuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=1200,
            duration_seconds=7200
        )
        response = self.client.post('/history/clear/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(WatchProgress.objects.filter(user=self.user).count(), 0)

    def test_analytics_view(self):
        self.client.login(username='watchuser', password='password123')
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=3600,
            duration_seconds=7200,
            completed=True
        )
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_hours', response.context)
        self.assertEqual(response.context['total_hours'], 1.0)
        self.assertEqual(response.context['completed_count'], 1)


