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
        
        gta = client._get_gta_vi_special()
        if not any(m.get('id') in [1744462, 1222222] or 'grand theft auto vi' in (m.get('title') or '').lower() for m in upcoming_releases):
            upcoming_releases.insert(0, gta)

        context['hero_movie'] = trending_movies[0] if trending_movies else (popular_movies[0] if popular_movies else None)
        context['trending_movies'] = trending_movies
        context['upcoming_releases'] = upcoming_releases
        context['popular_movies'] = popular_movies
        context['top_rated_movies'] = top_rated_movies
        context['popular_series'] = popular_series
        context['top_rated_series'] = top_rated_series
        context['action_movies'] = action_movies
        context['scifi_movies'] = scifi_movies
        context['animation_movies'] = animation_movies
        
        # User saved library IDs & My List quick preview rail
        my_list_preview = []
        custom_collections = []
        if self.request.user.is_authenticated:
            from apps.accounts.utils import get_active_profile
            profile = get_active_profile(self.request)
            context['user_saved_ids'] = set(LibraryItem.objects.filter(user=self.request.user, profile=profile).values_list('tmdb_id', flat=True))
            library_items = list(LibraryItem.objects.filter(user=self.request.user, profile=profile).order_by('-added_at')[:10])
            if library_items:
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(library_items), 6)) as ex:
                    def _fetch_lib_item(item):
                        if item.media_type == 'movie':
                            d = dict(client.get_movie(item.tmdb_id))
                            d['media_type'] = 'movie'
                            return d
                        else:
                            d = dict(client.get_tv(item.tmdb_id))
                            d['media_type'] = 'tv'
                            return d
                    my_list_preview = list(ex.map(_fetch_lib_item, library_items))
            
            custom_collections = list(CustomCollection.objects.filter(user=self.request.user, profile=profile).prefetch_related('items'))
        else:
            context['user_saved_ids'] = set()
        context['my_list_preview'] = my_list_preview
        context['custom_collections'] = custom_collections

        # Continue watching for logged in user (deduplicated by media_type + tmdb_id)
        continue_watching = []
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
                if key in seen:
                    continue
                seen.add(key)
                
                if p.media_type == 'movie':
                    data = dict(client.get_movie(p.tmdb_id))
                    data['display_title'] = data.get('title', f"Movie {p.tmdb_id}")
                    data['sub_label'] = "Movie"
                    data['watch_url'] = f"/watch/movie/{p.tmdb_id}/"
                else:
                    data = dict(client.get_tv(p.tmdb_id))
                    s_num = p.season or 1
                    ep_num = p.episode or 1
                    series_name = data.get('name', f"Series {p.tmdb_id}")
                    data['display_title'] = series_name
                    data['sub_label'] = f"S{s_num}:E{ep_num}"
                    data['watch_url'] = f"/watch/tv/{p.tmdb_id}/{s_num}/{ep_num}/"
                
                data['id'] = p.tmdb_id
                data['tmdb_id'] = p.tmdb_id
                data['media_type'] = p.media_type
                data['progress_percentage'] = p.progress_percentage
                data['position_seconds'] = p.position_seconds
                continue_watching.append(data)
                
                if len(continue_watching) >= 10:
                    break
                
        context['continue_watching'] = continue_watching

        # Personalized recommendations & Explainable "Because You Watched"
        context['recommended_for_you'] = engine.get_personalized_recommendations(self.request.user, profile=profile)
        because_data = engine.get_because_you_watched(self.request.user, profile=profile)
        if because_data:
            context['because_title'] = because_data['title']
            context['because_items'] = because_data['items']
        else:
            context['because_title'] = None
            context['because_items'] = []
            
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


