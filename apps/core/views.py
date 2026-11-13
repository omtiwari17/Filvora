import concurrent.futures
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.middleware.csrf import rotate_token
from apps.tmdb.client import TMDBClient
from apps.core.recommendations import RecommendationEngine
from apps.watch.models import WatchProgress
from apps.library.models import LibraryItem, CustomCollection

class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = TMDBClient()
        engine = RecommendationEngine()
        
        # Concurrently fetch all 9 homepage rails in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
            f_trending = executor.submit(client.get_trending_movies)
            f_popular_m = executor.submit(client.get_popular_movies)
            f_top_m = executor.submit(client.get_top_rated_movies)
            f_popular_s = executor.submit(client.get_popular_series)
            f_top_s = executor.submit(client.get_top_rated_series)
            f_action = executor.submit(client.get_action_movies)
            f_scifi = executor.submit(client.get_scifi_movies)
            f_animation = executor.submit(client.get_animation_movies)
            f_upcoming = executor.submit(client.get_movies_catalog, category='upcoming')

            trending_movies = f_trending.result()
            popular_movies = f_popular_m.result()
            top_rated_movies = f_top_m.result()
            popular_series = f_popular_s.result()
            top_rated_series = f_top_s.result()
            action_movies = f_action.result()
            scifi_movies = f_scifi.result()
            animation_movies = f_animation.result()
            upcoming_releases = f_upcoming.result()
        hero_pool = trending_movies if trending_movies else (popular_movies or [])
        context['hero_movie'] = hero_pool[0] if hero_pool else None
        context['hero_slides'] = hero_pool[:5]
        context['trending_movies'] = trending_movies
        context['upcoming_releases'] = upcoming_releases
        context['popular_movies'] = popular_movies
        context['top_rated_movies'] = top_rated_movies
        context['popular_series'] = popular_series
        context['top_rated_series'] = top_rated_series
        context['action_movies'] = action_movies
        context['scifi_movies'] = scifi_movies
        context['animation_movies'] = animation_movies
        
        has_catalog = bool(trending_movies or popular_movies or popular_series or top_rated_movies or action_movies)
        context['is_empty_catalog'] = not has_catalog
        context['is_offline'] = client.is_offline() or not has_catalog
        
        # User saved library IDs & My List quick preview rail
        my_list_preview = []
        custom_collections = []
        if self.request.user.is_authenticated:
            from apps.accounts.utils import get_active_profile
            profile = get_active_profile(self.request)
            context['user_saved_ids'] = set(LibraryItem.objects.filter(user=self.request.user, profile=profile).values_list('tmdb_id', flat=True))
            library_items = list(LibraryItem.objects.filter(user=self.request.user, profile=profile).order_by('-added_at')[:10])
            if library_items and not client.is_offline():
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(library_items), 6)) as ex:
                    def _fetch_lib_item(item):
                        summary = client.get_content_summary(item.tmdb_id, item.media_type)
                        d = dict(summary) if summary else {}
                        d['media_type'] = item.media_type
                        return d
                    my_list_preview = [i for i in ex.map(_fetch_lib_item, library_items) if i and i.get('id')]
            elif library_items and client.is_offline():
                for item in library_items:
                    my_list_preview.append({
                        'id': item.tmdb_id,
                        'tmdb_id': item.tmdb_id,
                        'title': f"{item.media_type.capitalize()} #{item.tmdb_id}",
                        'display_title': f"{item.media_type.capitalize()} #{item.tmdb_id}",
                        'media_type': item.media_type,
                        'poster_path': None
                    })
            
            custom_collections = list(CustomCollection.objects.filter(user=self.request.user, profile=profile).prefetch_related('items'))
        else:
            context['user_saved_ids'] = set()
        context['my_list_preview'] = my_list_preview
        context['custom_collections'] = custom_collections

        # Continue watching: persistent profile progress when signed in, or temporary session progress for guests
        continue_watching = []
        raw_cw_entries = []
        profile = None
        if self.request.user.is_authenticated:
            from apps.accounts.utils import get_active_profile
            profile = get_active_profile(self.request)
            progress_items = WatchProgress.objects.filter(
                user=self.request.user,
                profile=profile,
                completed=False,
                position_seconds__gt=5
            ).order_by('-updated_at')

            seen = set()
            for p in progress_items:
                key = (p.media_type, p.tmdb_id)
                if key not in seen:
                    seen.add(key)
                    raw_cw_entries.append({
                        'tmdb_id': p.tmdb_id,
                        'media_type': p.media_type,
                        'season': p.season,
                        'episode': p.episode,
                        'progress_percentage': p.progress_percentage,
                        'position_seconds': p.position_seconds,
                    })
                if len(raw_cw_entries) >= 10:
                    break
        else:
            from apps.watch.guest_session import get_guest_progress_map
            raw_cw_entries = list(get_guest_progress_map(self.request).values())

        if raw_cw_entries and not client.is_offline():
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(raw_cw_entries), 6)) as ex:
                def _fetch_cw_item(entry):
                    tid = entry['tmdb_id']
                    mtype = entry['media_type']
                    summary = client.get_content_summary(tid, mtype)
                    data = dict(summary) if summary else {}
                    if mtype == 'movie':
                        data['display_title'] = data.get('title', f"Movie {tid}")
                        data['sub_label'] = "Movie"
                        data['watch_url'] = f"/watch/movie/{tid}/"
                    else:
                        s_num = entry.get('season') or 1
                        ep_num = entry.get('episode') or 1
                        series_name = data.get('name', f"Series {tid}")
                        data['display_title'] = series_name
                        data['sub_label'] = f"S{s_num}:E{ep_num}"
                        data['watch_url'] = f"/watch/tv/{tid}/{s_num}/{ep_num}/"
                    data['id'] = tid
                    data['tmdb_id'] = tid
                    data['media_type'] = mtype
                    data['progress_percentage'] = entry['progress_percentage']
                    data['position_seconds'] = entry['position_seconds']
                    return data
                continue_watching = list(ex.map(_fetch_cw_item, raw_cw_entries))
        elif raw_cw_entries and client.is_offline():
            for entry in raw_cw_entries:
                tid = entry['tmdb_id']
                mtype = entry['media_type']
                s_num = entry.get('season') or 1
                ep_num = entry.get('episode') or 1
                continue_watching.append({
                    'id': tid,
                    'tmdb_id': tid,
                    'display_title': f"{mtype.capitalize()} #{tid}",
                    'sub_label': "Movie" if mtype == 'movie' else f"S{s_num}:E{ep_num}",
                    'media_type': mtype,
                    'watch_url': f"/watch/{mtype}/{tid}/" if mtype == 'movie' else f"/watch/tv/{tid}/{s_num}/{ep_num}/",
                    'progress_percentage': entry['progress_percentage'],
                    'position_seconds': entry['position_seconds'],
                    'poster_path': None
                })

        context['continue_watching'] = continue_watching
        context['is_guest_continue_watching'] = bool(continue_watching) and not self.request.user.is_authenticated

        # Personalized recommendations & Dynamic Contextual Rails
        if not client.is_offline():
            context['recommended_for_you'] = engine.get_personalized_recommendations(self.request.user, profile=profile)
            because_rails = engine.get_contextual_rails(self.request.user, profile=profile, max_rails=2)
            context['because_rails'] = because_rails
            if because_rails:
                context['because_title'] = because_rails[0]['title']
                context['because_items'] = because_rails[0]['items']
                context['because_label'] = because_rails[0].get('reason_prefix', 'Because You Liked')
            else:
                context['because_title'] = None
                context['because_items'] = []
                context['because_label'] = None
        else:
            context['recommended_for_you'] = []
            context['because_rails'] = []
            context['because_title'] = None
            context['because_items'] = []
            context['because_label'] = None
            
        return context


def csrf_failure(request, reason=""):
    """
    Custom branded CSRF failure view for Filvora.
    Gracefully handles stale tokens, token rotation after login, or multi-tab drift
    by issuing a fresh CSRF token and rendering a cinematic recovery page with auto-redirect.
    """
    from django.conf import settings
    # Rotate token and ensure fresh cookie is explicitly attached to the response
    rotate_token(request)
    new_token = request.META.get("CSRF_COOKIE")

    def _attach_csrf(resp):
        if new_token:
            resp.set_cookie(
                settings.CSRF_COOKIE_NAME,
                new_token,
                max_age=settings.CSRF_COOKIE_AGE,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=settings.CSRF_COOKIE_SECURE,
                httponly=settings.CSRF_COOKIE_HTTPONLY,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
        return resp

    # Check if request was from HTMX
    if request.headers.get('HX-Request'):
        response = HttpResponse(
            '<div class="p-4 bg-red-950/80 border border-red-800 rounded-xl text-red-200 text-sm">'
            'Session security token refreshed. Please try again.</div>',
            status=403
        )
        response['HX-Refresh'] = 'true'
        return _attach_csrf(response)

    # Check if request was JSON / API
    if request.headers.get('accept') == 'application/json' or request.content_type == 'application/json':
        response = JsonResponse({
            'status': 'error',
            'message': 'CSRF verification failed. Security token refreshed, please retry.',
            'reason': reason
        }, status=403)
        return _attach_csrf(response)

    # Standard browser navigation / form POST failure
    referer = request.META.get('HTTP_REFERER') or '/'
    target_url = '/accounts/login/' if '/accounts/' in request.path else referer

    context = {
        'reason': reason,
        'target_url': target_url,
        'path': request.path,
    }
    response = render(request, '403_csrf.html', context, status=403)
    return _attach_csrf(response)


class RecommendationsView(TemplateView):
    """
    Dedicated personalized recommendations hub presenting movie and series recommendations
    curated from the active profile's ratings, watch history, and affinity genres.
    """
    template_name = 'core/recommendations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = TMDBClient()
        engine = RecommendationEngine()

        media_filter = self.request.GET.get('type', 'all')
        if media_filter not in ['all', 'movie', 'tv']:
            media_filter = 'all'
        context['media_filter'] = media_filter

        profile = None
        user_saved_ids = set()
        if self.request.user.is_authenticated:
            from apps.accounts.utils import get_active_profile
            profile = get_active_profile(self.request)
            user_saved_ids = set(LibraryItem.objects.filter(user=self.request.user, profile=profile).values_list('tmdb_id', flat=True))

        context['active_profile'] = profile
        context['user_saved_ids'] = user_saved_ids
        context['is_offline'] = client.is_offline()

        rec_data = engine.get_dedicated_recommendations(
            user=self.request.user,
            profile=profile,
            media_filter=media_filter
        )

        context.update(rec_data)
        return context


def _read_latest_filvora_log(lines=60):
    """Helper to read recent lines from filvora.log across Termux and standard environments."""
    from pathlib import Path
    from django.conf import settings
    candidates = [
        Path.home() / 'filvora.log',
        Path('/data/data/com.termux/files/home/filvora.log'),
        settings.BASE_DIR / 'filvora.log',
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.readlines()
                    return ''.join(content[-lines:])
            except Exception:
                pass
    return "Server is actively running. (filvora.log is clean or running in direct console mode)."


class ServerHubView(TemplateView):
    """Secret Phone Server Access and Monitoring Hub."""
    template_name = 'core/server_hub.html'

    def get_context_data(self, **kwargs):
        import platform
        from pathlib import Path
        context = super().get_context_data(**kwargs)
        client = TMDBClient()

        is_android = 'com.termux' in str(Path.home()) or 'android' in platform.platform().lower()
        context['is_android'] = is_android
        context['system_os'] = 'Android 11 / MIUI 12.5.10 (Termux arm64)' if is_android else platform.platform()
        context['server_ip'] = '192.168.1.50'
        context['ssh_port'] = '8022'
        context['ssh_user'] = 'u0_a256'
        context['is_tmdb_online'] = not client.is_offline()
        context['recent_log'] = _read_latest_filvora_log(50)
        return context


def server_hub_log(request):
    """HTMX real-time polling endpoint for live server log streaming."""
    log_text = _read_latest_filvora_log(50)
    return HttpResponse(f"<pre class='font-mono text-xs text-emerald-400 whitespace-pre-wrap leading-relaxed select-text'>{log_text}</pre>")


def phone_server_access_view(request):
    """Direct secret view serving Phone Server Access.html from project root."""
    from pathlib import Path
    from django.conf import settings
    file_path = settings.BASE_DIR / 'Phone Server Access.html'
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse("Phone Server Access file not found.", status=404)

