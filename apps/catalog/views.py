from django.shortcuts import render
from django.http import HttpResponse
from apps.tmdb.client import TMDBClient
from apps.library.models import LibraryItem

def movie_browse(request):
    client = TMDBClient()
    movies = client.get_popular_movies()
    return render(request, 'catalog/movie_browse.html', {'movies': movies})

def movie_detail(request, tmdb_id):
    client = TMDBClient()
    movie = client.get_movie_details(tmdb_id)
    movie['display_title'] = movie.get('title', f"Movie {tmdb_id}")

    # Check if movie is saved in user's library
    in_library = False
    if request.user.is_authenticated:
        in_library = LibraryItem.objects.filter(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type='movie'
        ).exists()

    cast = []
    if 'credits' in movie and 'cast' in movie['credits']:
        cast = movie['credits']['cast'][:12]

    recommendations = []
    if 'recommendations' in movie and 'results' in movie['recommendations']:
        recommendations = movie['recommendations']['results'][:10]

    return render(request, 'catalog/movie_detail.html', {
        'movie': movie,
        'in_library': in_library,
        'cast': cast,
        'recommendations': recommendations,
    })

def series_browse(request):
    client = TMDBClient()
    series_list = client.get_popular_series()
    return render(request, 'catalog/series_browse.html', {'series_list': series_list})

def series_detail(request, tmdb_id):
    client = TMDBClient()
    series = client.get_tv_details(tmdb_id)
    series['display_title'] = series.get('name', f"Series {tmdb_id}")

    in_library = False
    if request.user.is_authenticated:
        in_library = LibraryItem.objects.filter(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type='tv'
        ).exists()

    cast = []
    if 'credits' in series and 'cast' in series['credits']:
        cast = series['credits']['cast'][:12]

    # Fetch initial Season 1 episodes
    seasons = [s for s in series.get('seasons', []) if s.get('season_number', 0) > 0]
    initial_season_num = seasons[0]['season_number'] if seasons else 1
    season_data = client.get_tv_season(tmdb_id, initial_season_num)
    episodes = season_data.get('episodes', [])

    return render(request, 'catalog/series_detail.html', {
        'series': series,
        'in_library': in_library,
        'cast': cast,
        'seasons': seasons,
        'current_season': initial_season_num,
        'episodes': episodes,
    })

def season_episodes(request, tmdb_id, season_number):
    client = TMDBClient()
    season_data = client.get_tv_season(tmdb_id, season_number)
    episodes = season_data.get('episodes', [])
    return render(request, 'catalog/partials/episode_list.html', {
        'tmdb_id': tmdb_id,
        'season_number': season_number,
        'episodes': episodes,
    })

def search_suggest(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return HttpResponse('')
    
    client = TMDBClient()
    results = client.search_multi(q)[:6]
    return render(request, 'catalog/partials/search_suggestions.html', {
        'results': results,
        'query': q,
    })

def search_results(request):
    q = request.GET.get('q', '').strip()
    client = TMDBClient()
    results = client.search_multi(q) if q else []
    return render(request, 'catalog/search_results.html', {
        'results': results,
        'query': q,
    })
