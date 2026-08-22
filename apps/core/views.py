from django.shortcuts import render
from django.views.generic import TemplateView
from apps.tmdb.client import TMDBClient

from apps.watch.models import WatchProgress

class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = TMDBClient()
        
        trending_movies = client.get_trending_movies()
        popular_movies = client.get_popular_movies()
        top_rated_movies = client.get_top_rated_movies()
        popular_series = client.get_popular_series()
        top_rated_series = client.get_top_rated_series()
        action_movies = client.get_action_movies()
        animation_movies = client.get_animation_movies()
        
        context['hero_movie'] = trending_movies[0] if trending_movies else (popular_movies[0] if popular_movies else None)
        context['trending_movies'] = trending_movies
        context['popular_movies'] = popular_movies
        context['top_rated_movies'] = top_rated_movies
        context['popular_series'] = popular_series
        context['top_rated_series'] = top_rated_series
        context['action_movies'] = action_movies
        context['animation_movies'] = animation_movies
        
        # Continue watching for logged in user
        continue_watching = []
        if self.request.user.is_authenticated:
            progress_items = WatchProgress.objects.filter(
                user=self.request.user,
                completed=False,
                position_seconds__gt=5
            ).order_by('-updated_at')[:10]
            
            for p in progress_items:
                if p.media_type == 'movie':
                    data = client.get_movie(p.tmdb_id)
                    data['display_title'] = data.get('title', f"Movie {p.tmdb_id}")
                else:
                    data = client.get_tv(p.tmdb_id)
                    data['display_title'] = data.get('name', f"Series {p.tmdb_id}")
                
                data['media_type'] = p.media_type
                data['progress_percentage'] = p.progress_percentage
                data['position_seconds'] = p.position_seconds
                continue_watching.append(data)
                
        context['continue_watching'] = continue_watching
        return context

