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


