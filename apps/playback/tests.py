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

    def test_watch_allows_guest_and_temporary_session_progress(self):
        """Unauthenticated guests can stream movies & series, resume temporarily in session, without saving forever or showing account-only tools."""
        # 1. Guest can open movie & TV series watch views directly
        res_movie = self.client.get('/watch/movie/157336/')
        self.assertEqual(res_movie.status_code, 200)
        movie_html = res_movie.content.decode('utf-8')
        self.assertNotIn('id="bookmark-modal"', movie_html)
        self.assertNotIn('hx-post="/library/toggle/"', movie_html)

        res_tv = self.client.get('/watch/tv/1399/1/2/')
        self.assertEqual(res_tv.status_code, 200)
        self.assertIsNotNone(res_tv.context['next_episode'])

        # 2. Save temporary guest playback progress (should NOT write WatchProgress DB row)
        save_resp = self.client.post(
            '/progress/save/',
            data=json.dumps({
                'tmdb_id': 157336,
                'media_type': 'movie',
                'position': 240,
                'duration': 7200,
            }),
            content_type='application/json'
        )
        self.assertEqual(save_resp.status_code, 200)
        self.assertTrue(save_resp.json().get('temporary'))
        self.assertEqual(WatchProgress.objects.count(), 0)

        # 3. Reopening player resumes at saved temporary position & Home Continue Watching displays Temporary Session
        res_resume = self.client.get('/watch/movie/157336/')
        self.assertEqual(res_resume.status_code, 200)
        self.assertEqual(res_resume.context['resume_position'], 240.0)

        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertTrue(res_home.context['is_guest_continue_watching'])
        self.assertEqual([c['tmdb_id'] for c in res_home.context['continue_watching']], [157336])
        self.assertContains(res_home, 'Temporary Session')

        # 4. Completing or removing clears temporary session entry (not kept permanently in history)
        comp_resp = self.client.post(
            '/progress/save/',
            data=json.dumps({
                'tmdb_id': 157336,
                'media_type': 'movie',
                'position': 6900,
                'duration': 7200,
            }),
            content_type='application/json'
        )
        self.assertEqual(comp_resp.status_code, 200)
        self.assertTrue(comp_resp.json().get('completed'))
        res_home_after = self.client.get('/')
        self.assertEqual(res_home_after.context['continue_watching'], [])
        self.assertEqual(WatchProgress.objects.count(), 0)

        # 5. Guest server preference & manual removal work temporarily in session without DB rows
        srv_resp = self.client.post(
            '/watch/server-success/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie', 'provider_id': 'autoembed'}),
            content_type='application/json'
        )
        self.assertEqual(srv_resp.status_code, 200)
        self.assertEqual(PlaybackServerPreference.objects.count(), 0)
        self.assertEqual(self.client.get('/watch/movie/157336/').context['current_server'], 'autoembed')

        self.client.post(
            '/progress/save/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie', 'position': 180, 'duration': 7200}),
            content_type='application/json'
        )
        rm_resp = self.client.post(
            '/progress/remove/',
            data=json.dumps({'tmdb_id': 157336, 'media_type': 'movie'}),
            content_type='application/json'
        )
        self.assertEqual(rm_resp.status_code, 200)
        self.assertEqual(self.client.get('/').context['continue_watching'], [])

        # 6. Permanent/account endpoints stay strictly login-gated for guests
        self.assertEqual(self.client.get('/library/').status_code, 302)
        self.assertEqual(self.client.get('/history/').status_code, 302)
        self.assertEqual(self.client.get('/watch/diagnostics/').status_code, 302)

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
        self.assertFalse(response.context['is_direct_jump'])
        self.assertIn('video_url', response.context)
        self.assertIsNotNone(response.context['next_provider'])

    def test_watch_direct_jump_timestamp(self):
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/movie/157336/?server=vidlink&t=340')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resume_position'], 340.0)
        self.assertTrue(response.context['is_direct_jump'])
        self.assertIn('startAt=340', response.context['video_url'])
        self.assertIn('t=340', response.context['video_url'])

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
        self.assertEqual(ordered[1].id, 'vidfast')

        # Test next provider fallback calculation
        next_after_vidlink = registry.get_next_provider('vidlink')
        self.assertEqual(next_after_vidlink.id, 'vidfast')

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

    def test_auto_failover_circular_sequence(self):
        """Ensures the failover cycle steps cleanly through all 6 servers without skipping."""
        ordered = registry.get_ordered_providers()
        self.assertEqual(len(ordered), 6)
        expected_chain = ['vidlink', 'vidfast', 'autoembed', 'vidsrc', '2embed', 'nontongo']
        for i, s_id in enumerate(expected_chain):
            next_expected = expected_chain[(i + 1) % len(expected_chain)]
            next_p = registry.get_next_provider(s_id)
            self.assertEqual(next_p.id, next_expected, f"Failed next provider for {s_id}")

    def test_watch_view_with_auto_failover_parameter(self):
        """Ensures watch view properly handles auto-switched incoming requests with auto=1."""
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/movie/157336/?server=vidfast&auto=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_server'], 'vidfast')
        self.assertEqual(response.context['next_provider'].id, 'autoembed')
        self.assertContains(response, 'id="auto-switch-hud"')
        self.assertContains(response, 'id="auto-failover-toggle-btn"')
        self.assertContains(response, 'initServerWatchdog')

    def test_watch_view_preserves_timestamp_on_auto_failover(self):
        """Ensures auto-switching carries the playback position into the new server embed URL."""
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/movie/157336/?server=vidsrc&t=2450&auto=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_server'], 'vidsrc')
        self.assertEqual(response.context['resume_position'], 2450.0)
        self.assertTrue(response.context['is_direct_jump'])
        self.assertIn('startAt=2450', response.context['video_url'])

    def test_report_server_success_missing_payload(self):
        self.client.login(username='playbackuser', password='password123')
        response = self.client.post(
            '/watch/server-success/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_report_server_success_get_rejected(self):
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/server-success/')
        self.assertEqual(response.status_code, 400)

    def test_multi_profile_server_preference_isolation(self):
        from apps.accounts.models import UserProfile
        p1 = UserProfile.objects.create(user=self.user, name='Streamer 1')
        p2 = UserProfile.objects.create(user=self.user, name='Streamer 2')

        self.client.login(username='playbackuser', password='password123')

        # Set preference on Profile 1
        session = self.client.session
        session['active_profile_id'] = p1.id
        session.save()
        PlaybackServerPreference.objects.create(
            user=self.user,
            profile=p1,
            tmdb_id=157336,
            media_type='movie',
            provider_id='vidfast'
        )

        # Set preference on Profile 2
        PlaybackServerPreference.objects.create(
            user=self.user,
            profile=p2,
            tmdb_id=157336,
            media_type='movie',
            provider_id='autoembed'
        )

        # Loading on Profile 1 picks vidfast
        res_p1 = self.client.get('/watch/movie/157336/')
        self.assertEqual(res_p1.context['current_server'], 'vidfast')

        # Switch to Profile 2 -> picks autoembed
        session['active_profile_id'] = p2.id
        session.save()
        res_p2 = self.client.get('/watch/movie/157336/')
        self.assertEqual(res_p2.context['current_server'], 'autoembed')

    def test_all_providers_movie_and_tv_urls(self):
        providers = registry.get_ordered_providers()
        self.assertEqual(len(providers), 6)
        for p in providers:
            # Movie
            movie_url = p.get_movie_url(157336)
            self.assertTrue(movie_url.startswith('http'))
            self.assertIn('157336', movie_url)
            # TV
            tv_url = p.get_tv_url(1399, 1, 1)
            self.assertTrue(tv_url.startswith('http'))
            self.assertIn('1399', tv_url)

    def test_vidfast_embed_focus_and_fullscreen_attributes(self):
        """Verifies Server 2 (VidFast) iframe attributes include fullscreen and focus preservation functions."""
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/movie/157336/?server=vidfast')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="filvora-embed-frame"')
        self.assertContains(response, 'allowfullscreen')
        self.assertContains(response, 'fullscreen *')
        self.assertContains(response, 'focusPlayerIframe')

    def test_watch_view_pause_failover_immunity(self):
        """Ensures pausing video suppresses auto-failover and watchdog freezes while paused."""
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/movie/157336/?server=vidlink')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'setPlaybackPausedState')
        self.assertContains(response, 'checkEmbedPauseSignal')
        self.assertContains(response, 'checkEmbedPlaySignal')
        self.assertContains(response, 'lastUserPauseTime')
        self.assertContains(response, 'lastIframeInteractionTime')
        self.assertContains(response, 'triggerAutoSwitch(reason = \'Server not responding\')')

    def test_autoplay_countdown_and_fullscreen_overlay_resilience(self):
        """Verifies that TV episode watch view includes the Up Next autoplay countdown modal, high z-index and active guard."""
        self.client.login(username='playbackuser', password='password123')
        response = self.client.get('/watch/tv/1399/1/2/?server=vidfast')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['next_episode'])
        content = response.content.decode('utf-8')
        self.assertIn('id="autoplay-modal"', content)
        self.assertIn('id="autoplay-countdown"', content)
        self.assertIn('id="autoplay-progress-bar"', content)
        self.assertIn('isAutoplayActive', content)
        self.assertIn(':fullscreen #autoplay-modal', content)
        self.assertIn('.is-fullscreen #autoplay-modal', content)
        self.assertIn('embed-fullscreen-hotspot', content)

    def test_phase6_in_player_episode_drawer_and_partial_endpoint(self):
        """Verifies Phase 6 in-player slide-over episode drawer, fullscreen layering, and HTMX episode partial."""
        self.client.login(username='playbackuser', password='password123')

        res_tv = self.client.get('/watch/tv/1399/1/2/?server=vidlink')
        self.assertEqual(res_tv.status_code, 200)
        html_tv = res_tv.content.decode('utf-8')
        self.assertIn('id="episode-drawer-btn"', html_tv)
        self.assertIn('id="player-episode-drawer"', html_tv)
        self.assertIn('id="drawer-episodes-skeleton"', html_tv)
        self.assertIn('id="drawer-episodes-list"', html_tv)
        self.assertIn(':fullscreen #player-episode-drawer', html_tv)
        self.assertIn('openEpisodeDrawer', html_tv)
        self.assertIn('drawer_episodes', res_tv.context)

        res_partial = self.client.get('/watch/tv/1399/episodes/1/?server=vidlink&active_season=1&active_episode=2')
        self.assertEqual(res_partial.status_code, 200)
        html_partial = res_partial.content.decode('utf-8')
        self.assertIn('S1 E2', html_partial)
        self.assertIn('Playing', html_partial)
        self.assertIn('?server=vidlink', html_partial)

        res_movie = self.client.get('/watch/movie/157336/?server=vidlink')
        self.assertEqual(res_movie.status_code, 200)
        html_movie = res_movie.content.decode('utf-8')
        self.assertNotIn('id="player-episode-drawer"', html_movie)
        self.assertNotIn('id="episode-drawer-btn"', html_movie)

    def test_watch_guest_account_actions_prompt_modal(self):
        """Verifies player watchlist and bookmark buttons stay visible to guests and invoke promptAuthModal."""
        self.client.logout()

        # 1. Unauthenticated guest watch view renders buttons with promptAuthModal triggers
        res = self.client.get('/watch/movie/157336/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn("promptAuthModal('Add to My List'", html)
        self.assertIn("promptAuthModal('Scene Bookmarks'", html)
        self.assertIn('id="auth-prompt-modal"', html)
        self.assertIn('Sign In to Continue', html)

        # 2. Authenticated user has active HTMX watchlist button and opens bookmark modal
        self.client.login(username='playbackuser', password='password123')
        res_auth = self.client.get('/watch/movie/157336/')
        self.assertEqual(res_auth.status_code, 200)
        html_auth = res_auth.content.decode('utf-8')
        self.assertIn('hx-post="/library/toggle/"', html_auth)
        self.assertIn('openBookmarkModal()', html_auth)






