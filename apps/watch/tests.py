import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.watch.models import WatchProgress, UserRating


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

    def test_analytics_view_season_breakdown(self):
        self.client.login(username='watchuser', password='password123')
        # S1 E1: 3600s
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=1399,
            media_type='tv',
            season=1,
            episode=1,
            position_seconds=3600,
            duration_seconds=3600,
            completed=True
        )
        # S2 E1: 1800s
        WatchProgress.objects.create(
            user=self.user,
            tmdb_id=1399,
            media_type='tv',
            season=2,
            episode=1,
            position_seconds=1800,
            duration_seconds=3600,
            completed=False
        )
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('series_season_list', response.context)
        self.assertTrue(len(response.context['series_season_list']) >= 1)
        series_item = response.context['series_season_list'][0]
        self.assertEqual(series_item['id'], 1399)
        self.assertEqual(len(series_item['formatted_seasons']), 2)
        self.assertEqual(series_item['formatted_seasons'][0]['season_number'], 1)
        self.assertEqual(series_item['formatted_seasons'][0]['play_time_str'], '1.0 hrs')
        self.assertEqual(series_item['formatted_seasons'][1]['season_number'], 2)
        self.assertEqual(series_item['formatted_seasons'][1]['play_time_str'], '30 mins')


class UserRatingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='rateuser', password='password123')

    def test_rate_content_json(self):
        self.client.login(username='rateuser', password='password123')
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 4}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['score'], 4)
        self.assertTrue(data['created'])
        self.assertTrue(UserRating.objects.filter(user=self.user, tmdb_id=550, score=4).exists())

    def test_rate_content_update(self):
        self.client.login(username='rateuser', password='password123')
        UserRating.objects.create(user=self.user, tmdb_id=550, media_type='movie', score=3)
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 5}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['score'], 5)
        self.assertFalse(data['created'])
        self.assertEqual(UserRating.objects.get(user=self.user, tmdb_id=550).score, 5)

    def test_rate_content_invalid_score(self):
        self.client.login(username='rateuser', password='password123')
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 6}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_rate_content_zero_score(self):
        self.client.login(username='rateuser', password='password123')
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 0}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_rating(self):
        self.client.login(username='rateuser', password='password123')
        UserRating.objects.create(user=self.user, tmdb_id=550, media_type='movie', score=4)
        response = self.client.post(
            '/progress/rate/remove/',
            data=json.dumps({'tmdb_id': 550, 'media_type': 'movie'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserRating.objects.filter(user=self.user, tmdb_id=550).exists())

    def test_rate_requires_login(self):
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 4}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_rate_tv_series(self):
        self.client.login(username='rateuser', password='password123')
        payload = {'tmdb_id': 1399, 'media_type': 'tv', 'score': 5}
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserRating.objects.filter(user=self.user, tmdb_id=1399, media_type='tv', score=5).exists())

    def test_unique_constraint(self):
        self.client.login(username='rateuser', password='password123')
        UserRating.objects.create(user=self.user, tmdb_id=550, media_type='movie', score=3)
        # Rating same content again should update, not create duplicate
        payload = {'tmdb_id': 550, 'media_type': 'movie', 'score': 5}
        self.client.post(
            '/progress/rate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(UserRating.objects.filter(user=self.user, tmdb_id=550, media_type='movie').count(), 1)




