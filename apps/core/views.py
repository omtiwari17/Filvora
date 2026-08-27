import concurrent.futures
from django.shortcuts import render
from django.views.generic import TemplateView
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
            context['user_saved_ids'] = set(LibraryItem.objects.filter(user=self.request.user).values_list('tmdb_id', flat=True))
            library_items = list(LibraryItem.objects.filter(user=self.request.user).order_by('-added_at')[:10])
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
            
            custom_collections = list(CustomCollection.objects.filter(user=self.request.user).prefetch_related('items'))
        else:
            context['user_saved_ids'] = set()
        context['my_list_preview'] = my_list_preview
        context['custom_collections'] = custom_collections

        # Continue watching for logged in user (deduplicated by media_type + tmdb_id)
        continue_watching = []
        if self.request.user.is_authenticated:
            progress_items = WatchProgress.objects.filter(
                user=self.request.user,
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
        context['recommended_for_you'] = engine.get_personalized_recommendations(self.request.user)
        because_data = engine.get_because_you_watched(self.request.user)
        if because_data:
            context['because_title'] = because_data['title']
            context['because_items'] = because_data['items']
        else:
            context['because_title'] = None
            context['because_items'] = []
            
        return context


