from django.shortcuts import render
from django.views.generic import TemplateView
from apps.tmdb.client import TMDBClient

class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = TMDBClient()
        
        trending_movies = client.get_trending_movies()
        popular_series = client.get_popular_series()
        
        context['hero_movie'] = trending_movies[0] if trending_movies else None
        context['trending_movies'] = trending_movies
        context['popular_series'] = popular_series
        
        return context
