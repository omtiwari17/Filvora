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

    def test_multi_profile_history_and_ratings_isolation(self):
        """Verify that WatchProgress and UserRatings are strictly segregated between profiles."""
        from apps.accounts.models import UserProfile
        p1 = UserProfile.objects.create(user=self.user, name='Profile One', is_kids=False)
        p2 = UserProfile.objects.create(user=self.user, name='Profile Two', is_kids=True)

        self.client.login(username='rateuser', password='password123')

        # Select Profile 1
        session = self.client.session
        session['active_profile_id'] = p1.id
        session.save()

        # Save progress and rate title on Profile 1
        self.client.post(
            '/progress/save/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie', 'position': 300, 'duration': 6000}),
            content_type='application/json'
        )
        self.client.post(
            '/progress/rate/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie', 'score': 5}),
            content_type='application/json'
        )

        # Verify Profile 1 has progress & rating
        self.assertTrue(WatchProgress.objects.filter(user=self.user, profile=p1, tmdb_id=157336).exists())
        self.assertTrue(UserRating.objects.filter(user=self.user, profile=p1, tmdb_id=157336, score=5).exists())

        # Switch to Profile 2
        session['active_profile_id'] = p2.id
        session.save()

        # Profile 2 history should be completely empty
        res = self.client.get('/history/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_items'], 0)
        self.assertEqual(res.context['total_rated'], 0)

        # Rate on Profile 2 with a different score
        self.client.post(
            '/progress/rate/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie', 'score': 2}),
            content_type='application/json'
        )
        self.assertEqual(UserRating.objects.get(user=self.user, profile=p1, tmdb_id=157336).score, 5)
        self.assertEqual(UserRating.objects.get(user=self.user, profile=p2, tmdb_id=157336).score, 2)

    def test_save_progress_below_threshold_ignored(self):
        self.client.login(username=self.user.username, password='password123')
        payload = {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'position': 10, # below 15s threshold
            'duration': 6000
        }
        response = self.client.post(
            '/progress/save/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ignored')
        self.assertFalse(WatchProgress.objects.filter(user=self.user, tmdb_id=157336).exists())

    def test_save_progress_tv_series(self):
        self.client.login(username=self.user.username, password='password123')
        payload = {
            'tmdb_id': 1399,
            'media_type': 'tv',
            'season': 3,
            'episode': 9,
            'position': 1800,
            'duration': 3600
        }
        response = self.client.post(
            '/progress/save/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        wp = WatchProgress.objects.filter(user=self.user, tmdb_id=1399, season=3, episode=9).first()
        self.assertIsNotNone(wp)
        self.assertEqual(wp.position_seconds, 1800)

    def test_save_progress_get_rejected(self):
        self.client.login(username=self.user.username, password='password123')
        response = self.client.get('/progress/save/')
        self.assertEqual(response.status_code, 400)

    def test_clear_history_get_safely_redirects(self):
        self.client.login(username=self.user.username, password='password123')
        WatchProgress.objects.create(

            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            position_seconds=1200,
            duration_seconds=7200
        )
        # GET should not delete history
        response = self.client.get('/history/clear/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WatchProgress.objects.filter(user=self.user).exists())

    def test_rate_content_missing_fields(self):
        self.client.login(username='rateuser', password='password123')
        response = self.client.post(
            '/progress/rate/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_rate_content_htmx_partial(self):
        self.client.login(username='rateuser', password='password123')
        response = self.client.post(
            '/progress/rate/',
            {'tmdb_id': 550, 'media_type': 'movie', 'score': 4},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('rating-container', response.content.decode('utf-8'))

    def test_analytics_empty_state(self):
        """Verifies analytics view displays clean empty state when user has zero watch history."""
        self.client.force_login(self.user)
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('No Streaming Activity Yet', html)
        self.assertIn('Start Streaming', html)
        self.assertNotIn('None Aficionado', html)

    def test_toggle_watched_mark_and_unmark_movie(self):
        """Verifies 1-click toggle_watched marks movie as watched and second click unmarks it."""
        self.client.login(username='rateuser', password='password123')
        # 1. Mark as watched
        res1 = self.client.post('/progress/mark-watched/', {
            'tmdb_id': 550,
            'media_type': 'movie',
            'variant': 'card'
        })
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(WatchProgress.objects.filter(user=self.user, tmdb_id=550, media_type='movie', completed=True).exists())

        # 2. Unmark as watched
        res2 = self.client.post('/progress/mark-watched/', {
            'tmdb_id': 550,
            'media_type': 'movie',
            'variant': 'card'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(WatchProgress.objects.filter(user=self.user, tmdb_id=550, media_type='movie', completed=True).exists())

    def test_toggle_watched_tv_series(self):
        """Verifies 1-click toggle_watched marks a TV series as watched."""
        self.client.login(username='rateuser', password='password123')
        res = self.client.post('/progress/mark-watched/', {
            'tmdb_id': 1399,
            'media_type': 'tv',
            'variant': 'card'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(WatchProgress.objects.filter(user=self.user, tmdb_id=1399, media_type='tv', completed=True).exists())

    def test_toggle_watched_htmx_card_variant(self):
        """Verifies HTMX card variant returns card_watch_button with correct tooltips and classes."""
        self.client.login(username='rateuser', password='password123')
        res = self.client.post(
            '/progress/mark-watched/',
            {'tmdb_id': 550, 'media_type': 'movie', 'variant': 'card'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('card-watch-btn-movie-550', content)
        self.assertIn('Watched (Click to unmark)', content)
        self.assertIn('bg-emerald-600', content)

    def test_toggle_watched_htmx_detail_variant(self):
        """Verifies HTMX detail variant returns detail_watch_button with text badge."""
        self.client.login(username='rateuser', password='password123')
        res = self.client.post(
            '/progress/mark-watched/',
            {'tmdb_id': 550, 'media_type': 'movie', 'variant': 'detail'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('detail-watch-btn-550', content)
        self.assertIn('Watched', content)
        self.assertIn('bg-emerald-600', content)

    def test_rate_content_card_variant_htmx(self):
        """Verifies rating content with variant='card' returns card_rating_button with score badge."""
        self.client.login(username='rateuser', password='password123')
        res = self.client.post(
            '/progress/rate/',
            {'tmdb_id': 550, 'media_type': 'movie', 'score': 5, 'variant': 'card'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('card-rate-movie-550', content)
        self.assertIn('Your rating: 5/5', content)
        self.assertIn('text-yellow-400', content)

    def test_remove_rating_card_variant_htmx(self):
        """Verifies removing rating with variant='card' returns unrated card_rating_button."""
        self.client.login(username='rateuser', password='password123')
        UserRating.objects.create(user=self.user, tmdb_id=550, media_type='movie', score=4)
        res = self.client.post(
            '/progress/rate/remove/',
            {'tmdb_id': 550, 'media_type': 'movie', 'variant': 'card'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('card-rate-movie-550', content)
        self.assertIn('Rate with stars', content)
        self.assertFalse(UserRating.objects.filter(user=self.user, tmdb_id=550).exists())

    def test_multi_profile_watch_context_processor(self):
        """Verifies user_watch_context strictly segregates watched IDs and ratings across profiles."""
        from apps.accounts.models import UserProfile
        from apps.watch.context_processors import user_watch_context
        from django.test.client import RequestFactory

        p1 = UserProfile.objects.create(user=self.user, name="Profile 1")
        p2 = UserProfile.objects.create(user=self.user, name="Profile 2")

        # Set p1 data
        WatchProgress.objects.create(user=self.user, profile=p1, tmdb_id=100, media_type='movie', completed=True)
        UserRating.objects.create(user=self.user, profile=p1, tmdb_id=100, media_type='movie', score=5)

        # Set p2 data
        WatchProgress.objects.create(user=self.user, profile=p2, tmdb_id=200, media_type='tv', completed=True)
        UserRating.objects.create(user=self.user, profile=p2, tmdb_id=200, media_type='tv', score=3)

        factory = RequestFactory()

        # Request for p1
        req1 = factory.get('/')
        req1.user = self.user
        req1.session = {'active_profile_id': p1.id}
        ctx1 = user_watch_context(req1)
        self.assertIn(100, ctx1['user_watched_movie_ids'])
        self.assertNotIn(200, ctx1['user_watched_ids'])
        self.assertEqual(ctx1['user_movie_ratings'].get(100), 5)
        self.assertIsNone(ctx1['user_tv_ratings'].get(200))

        # Request for p2
        req2 = factory.get('/')
        req2.user = self.user
        req2.session = {'active_profile_id': p2.id}
        ctx2 = user_watch_context(req2)
        self.assertIn(200, ctx2['user_watched_tv_ids'])
        self.assertNotIn(100, ctx2['user_watched_ids'])
        self.assertEqual(ctx2['user_tv_ratings'].get(200), 3)
        self.assertIsNone(ctx2['user_movie_ratings'].get(100))

    def test_toggle_collection_watched_batch(self):
        """Test batch marking an entire franchise saga as watched and unmarking it."""
        from apps.accounts.models import UserProfile
        self.client.force_login(self.user)
        profile = UserProfile.objects.create(user=self.user, name="Saga Fan")
        session = self.client.session
        session['active_profile_id'] = profile.id
        session.save()

        movie_ids = [438631, 693134]  # Dune Part 1 & Dune Part 2
        payload = {
            'collection_id': 726871,
            'movie_ids': '438631,693134',
        }

        # 1. First toggle -> marks all as completed
        res = self.client.post('/progress/collection/mark-watched/', data=payload, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.assertIn('sagaWatchedChanged', res.headers.get('HX-Trigger', ''))

        for mid in movie_ids:
            p = WatchProgress.objects.get(user=self.user, profile=profile, tmdb_id=mid, media_type='movie')
            self.assertTrue(p.completed)

        # 2. Second toggle -> unmarks all
        res2 = self.client.post('/progress/collection/mark-watched/', data=payload, HTTP_HX_REQUEST='true')
        self.assertEqual(res2.status_code, 200)
        for mid in movie_ids:
            p_exists = WatchProgress.objects.filter(user=self.user, profile=profile, tmdb_id=mid, media_type='movie', completed=True).exists()
            self.assertFalse(p_exists)

    def test_rate_collection_batch(self):
        """Test batch rating all movies in a franchise collection (1-5 stars)."""
        from apps.accounts.models import UserProfile
        self.client.force_login(self.user)
        profile = UserProfile.objects.create(user=self.user, name="Saga Critic")
        session = self.client.session
        session['active_profile_id'] = profile.id
        session.save()

        movie_ids = [438631, 693134]
        payload = {
            'collection_id': 726871,
            'movie_ids': '438631,693134',
            'score': 5,
        }

        res = self.client.post('/progress/collection/rate/', data=payload, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.assertIn('sagaRatingChanged', res.headers.get('HX-Trigger', ''))

        for mid in movie_ids:
            rating = UserRating.objects.get(user=self.user, profile=profile, tmdb_id=mid, media_type='movie')
            self.assertEqual(rating.score, 5)

    def test_remove_collection_rating_batch(self):
        """Test clearing batch ratings for all movies in a franchise collection."""
        from apps.accounts.models import UserProfile
        self.client.force_login(self.user)
        profile = UserProfile.objects.create(user=self.user, name="Saga Neutral")
        session = self.client.session
        session['active_profile_id'] = profile.id
        session.save()

        movie_ids = [438631, 693134]
        for mid in movie_ids:
            UserRating.objects.create(user=self.user, profile=profile, tmdb_id=mid, media_type='movie', score=4)

        payload = {
            'collection_id': 726871,
            'movie_ids': '438631,693134',
        }
        res = self.client.post('/progress/collection/rate/remove/', data=payload, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)

        ratings_count = UserRating.objects.filter(user=self.user, profile=profile, tmdb_id__in=movie_ids).count()
        self.assertEqual(ratings_count, 0)

    def test_watch_date_single_day_display(self):
        """Test single-day watch date display formatting for completed and in-progress titles."""
        from django.utils import timezone
        import datetime
        dt = timezone.make_aware(datetime.datetime(2026, 9, 18, 14, 30))
        p = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=101,
            media_type='movie',
            completed=True,
            created_at=dt,
            completed_at=dt + datetime.timedelta(hours=2)
        )
        self.assertFalse(p.is_multi_day)
        self.assertEqual(p.watch_date_display, "Sep 18, 2026")
        self.assertEqual(p.watch_date_tooltip, "Completed on Sep 18, 2026")

    def test_watch_date_multi_day_display(self):
        """Test multi-day date span formatting across same-month, cross-month, and cross-year."""
        from django.utils import timezone
        import datetime

        # Same month span
        d1 = timezone.make_aware(datetime.datetime(2026, 9, 15, 10, 0))
        d2 = timezone.make_aware(datetime.datetime(2026, 9, 18, 20, 0))
        p_same_month = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=102,
            media_type='movie',
            completed=True,
            created_at=d1,
            completed_at=d2
        )
        self.assertTrue(p_same_month.is_multi_day)
        self.assertEqual(p_same_month.watch_date_display, "Sep 15 – 18, 2026")
        self.assertEqual(p_same_month.watch_date_tooltip, "Started Sep 15, 2026 • Completed Sep 18, 2026")

        # Cross month span
        d3 = timezone.make_aware(datetime.datetime(2026, 8, 28, 10, 0))
        d4 = timezone.make_aware(datetime.datetime(2026, 9, 2, 12, 0))
        p_cross_month = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=103,
            media_type='movie',
            completed=True,
            created_at=d3,
            completed_at=d4
        )
        self.assertTrue(p_cross_month.is_multi_day)
        self.assertEqual(p_cross_month.watch_date_display, "Aug 28 – Sep 02, 2026")

        # Cross year span
        d5 = timezone.make_aware(datetime.datetime(2025, 12, 28, 10, 0))
        d6 = timezone.make_aware(datetime.datetime(2026, 1, 2, 12, 0))
        p_cross_year = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=104,
            media_type='movie',
            completed=True,
            created_at=d5,
            completed_at=d6
        )
        self.assertTrue(p_cross_year.is_multi_day)
        self.assertEqual(p_cross_year.watch_date_display, "Dec 28, 2025 – Jan 02, 2026")

    def test_watch_date_in_progress_multi_day(self):
        """Test in-progress multi-day span formatting."""
        from django.utils import timezone
        import datetime
        d1 = timezone.make_aware(datetime.datetime(2026, 9, 10, 10, 0))
        d2 = timezone.make_aware(datetime.datetime(2026, 9, 14, 18, 0))
        p = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=105,
            media_type='movie',
            completed=False,
            created_at=d1
        )
        WatchProgress.objects.filter(id=p.id).update(updated_at=d2)
        p.refresh_from_db()
        self.assertTrue(p.is_multi_day)
        self.assertEqual(p.watch_date_display, "Sep 10 – 14, 2026")
        self.assertEqual(p.watch_date_tooltip, "Started Sep 10, 2026 • Last played Sep 14, 2026")

    def test_completed_at_timestamp_lifecycle(self):
        """Test completed_at lifecycle in toggle_watched and save_progress."""
        self.client.force_login(self.user)
        # 1. Toggle watched -> sets completed_at
        res = self.client.post('/progress/mark-watched/', data={'tmdb_id': 106, 'media_type': 'movie'}, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        p = WatchProgress.objects.get(user=self.user, tmdb_id=106)
        self.assertTrue(p.completed)
        self.assertIsNotNone(p.completed_at)

        # 2. Toggle watched again on full-watched record -> deletes record
        res2 = self.client.post('/progress/mark-watched/', data={'tmdb_id': 106, 'media_type': 'movie'}, HTTP_HX_REQUEST='true')
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(WatchProgress.objects.filter(user=self.user, tmdb_id=106).exists())

        # 3. Test save_progress setting completed_at when completed, and clearing when in progress
        payload_completed = {
            'tmdb_id': 108,
            'media_type': 'movie',
            'position': 5800,
            'duration': 6000
        }
        res3 = self.client.post('/progress/save/', data=json.dumps(payload_completed), content_type='application/json')
        self.assertEqual(res3.status_code, 200)
        p_saved = WatchProgress.objects.get(user=self.user, tmdb_id=108)
        self.assertTrue(p_saved.completed)
        self.assertIsNotNone(p_saved.completed_at)

        # In-progress save (<90%) clears completed_at
        payload_inprogress = {
            'tmdb_id': 108,
            'media_type': 'movie',
            'position': 1200,
            'duration': 6000
        }
        res4 = self.client.post('/progress/save/', data=json.dumps(payload_inprogress), content_type='application/json')
        self.assertEqual(res4.status_code, 200)
        p_saved.refresh_from_db()
        self.assertFalse(p_saved.completed)
        self.assertIsNone(p_saved.completed_at)

    def test_history_view_watch_date_enrichment(self):
        """Test that history view enriches cards with watch_date_display and tooltip."""
        self.client.force_login(self.user)
        p = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=107,
            media_type='movie',
            completed=True,
            position_seconds=5400,
            duration_seconds=5400
        )
        res = self.client.get('/history/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, p.watch_date_display)
        # Check rendered calendar pill
        self.assertContains(res, 'viewBox="0 0 24 24"')

    def test_watch_date_legacy_and_chronological_clamping(self):
        """Test that if created_at > updated_at or completed_at is None, properties clamp cleanly."""
        from django.utils import timezone
        import datetime

        d_past = timezone.make_aware(datetime.datetime(2026, 9, 15, 16, 25))
        d_future_err = timezone.make_aware(datetime.datetime(2026, 9, 18, 17, 5))

        # Erroneous future created_at with completed=True and completed_at=None
        p = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=109,
            media_type='movie',
            completed=True,
            created_at=d_future_err
        )
        WatchProgress.objects.filter(id=p.id).update(updated_at=d_past)
        p.refresh_from_db()

        # Effective start dt should clamp to effective end dt (d_past)
        self.assertEqual(p.effective_end_dt.date(), d_past.date())
        self.assertEqual(p.effective_start_dt.date(), d_past.date())
        self.assertFalse(p.is_multi_day)
        self.assertEqual(p.watch_date_display, "Sep 15, 2026")
        self.assertEqual(p.watch_date_tooltip, "Completed on Sep 15, 2026")

    def test_watch_date_single_sitting_supergirl_scenario(self):
        """Test single-sitting scenario where a movie is watched and completed on the same date."""
        from django.utils import timezone
        import datetime

        d_watch = timezone.make_aware(datetime.datetime(2026, 9, 15, 20, 0))
        p = WatchProgress.objects.create(
            user=self.user,
            tmdb_id=1081003,  # Supergirl
            media_type='movie',
            completed=True,
            created_at=d_watch,
            completed_at=d_watch + datetime.timedelta(hours=2)
        )
        self.assertFalse(p.is_multi_day)
        self.assertEqual(p.watch_date_display, "Sep 15, 2026")
        self.assertEqual(p.watch_date_tooltip, "Completed on Sep 15, 2026")









