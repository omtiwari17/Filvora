from django.shortcuts import render
from django.http import HttpResponse
from apps.tmdb.client import TMDBClient
from apps.library.models import LibraryItem

def get_pagination_context(page, total_pages=500):
    try:
        current = max(1, int(page or 1))
    except (ValueError, TypeError):
        current = 1
    start_p = max(1, current - 2)
    end_p = min(total_pages, current + 2)
    page_numbers = list(range(start_p, end_p + 1))
    return {
        'current_page': current,
        'has_prev': current > 1,
        'prev_page': current - 1,
        'has_next': current < total_pages,
        'next_page': current + 1,
        'page_numbers': page_numbers,
    }

def movie_browse(request):
    client = TMDBClient()
    category = request.GET.get('category', 'popular')
    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort', 'popularity.desc')
    page = request.GET.get('page', '1')
    kids_mode = is_kids_profile(request)

    movies = client.get_movies_catalog(
        category=category,
        genre_id=genre_id,
        sort_by=sort_by,
        page=page,
        kids_only=kids_mode
    )
    genres = client.get_genres_list()

    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))

    pagination = get_pagination_context(page)

    return render(request, 'catalog/movie_browse.html', {
        'movies': movies,
        'genres': genres,
        'selected_category': category,
        'selected_genre': genre_id,
        'selected_sort': sort_by,
        'pagination': pagination,
        'user_saved_ids': user_saved_ids
    })

def movie_detail(request, tmdb_id):
    client = TMDBClient()
    movie = client.get_movie_details(tmdb_id)
    movie['display_title'] = movie.get('title', f"Movie {tmdb_id}")

    # Check if movie is saved in user's library
    in_library = False
    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))
        in_library = int(tmdb_id) in user_saved_ids

    cast = []
    if 'credits' in movie and 'cast' in movie['credits']:
        cast = movie['credits']['cast'][:12]

    recommendations = []
    if 'recommendations' in movie and 'results' in movie['recommendations']:
        recommendations = movie['recommendations']['results'][:10]

    return render(request, 'catalog/movie_detail.html', {
        'movie': movie,
        'in_library': in_library,
        'user_saved_ids': user_saved_ids,
        'cast': cast,
        'recommendations': recommendations,
    })

def series_browse(request):
    client = TMDBClient()
    category = request.GET.get('category', 'popular')
    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort', 'popularity.desc')
    page = request.GET.get('page', '1')
    kids_mode = is_kids_profile(request)

    series_list = client.get_series_catalog(
        category=category,
        genre_id=genre_id,
        sort_by=sort_by,
        page=page,
        kids_only=kids_mode
    )
    genres = client.get_genres_list()

    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))

    pagination = get_pagination_context(page)

    return render(request, 'catalog/series_browse.html', {
        'series_list': series_list,
        'genres': genres,
        'selected_category': category,
        'selected_genre': genre_id,
        'selected_sort': sort_by,
        'pagination': pagination,
        'user_saved_ids': user_saved_ids
    })


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
    categorized = client.search_categorized(q)
    return render(request, 'catalog/partials/search_suggestions.html', {
        'categorized': categorized,
        'movies': categorized['movies'][:4],
        'series': categorized['series'][:4],
        'people': categorized['people'][:3],
        'has_results': bool(categorized['movies'] or categorized['series'] or categorized['people']),
        'query': q,
    })

def search_results(request):
    q = request.GET.get('q', '').strip()
    client = TMDBClient()
    results = client.search_multi(q) if q else []
    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))
    return render(request, 'catalog/search_results.html', {
        'results': results,
        'query': q,
        'user_saved_ids': user_saved_ids,
    })

def is_kids_profile(request):
    if not request.user.is_authenticated:
        return False
    from apps.accounts.models import UserProfile
    profile_id = request.session.get('active_profile_id')
    if profile_id:
        p = UserProfile.objects.filter(id=profile_id, user=request.user).first()
        if p and p.is_kids:
            return True
    return False

def discover(request):
    client = TMDBClient()
    media_type = request.GET.get('type', 'movie')
    if media_type not in ['movie', 'tv']:
        media_type = 'movie'
    genre_id = request.GET.get('genre')
    year = request.GET.get('year')
    min_rating = request.GET.get('rating')
    mood = request.GET.get('mood')
    language = request.GET.get('language')
    certification = request.GET.get('certification')
    sort_by = request.GET.get('sort', 'popularity.desc')
    kids_mode = is_kids_profile(request)

    results = client.discover_content(
        media_type=media_type,
        genre_id=genre_id,
        year=year,
        min_rating=min_rating,
        mood=mood,
        language=language,
        certification=certification,
        kids_only=kids_mode,
        sort_by=sort_by
    )

    genres = client.get_genres_list()
    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))

    return render(request, 'catalog/discover.html', {
        'results': results,
        'genres': genres,
        'media_type': media_type,
        'selected_genre': genre_id,
        'selected_year': year,
        'selected_rating': min_rating,
        'selected_mood': mood,
        'selected_language': language,
        'selected_certification': certification,
        'selected_sort': sort_by,
        'is_kids_mode': kids_mode,
        'user_saved_ids': user_saved_ids,
    })

def surprise_me(request):
    from django.shortcuts import redirect
    client = TMDBClient()
    media_type = request.GET.get('type', 'movie')
    genre_id = request.GET.get('genre')
    mood = request.GET.get('mood')
    pick = client.get_surprise_title(media_type=media_type, genre_id=genre_id, mood=mood)
    
    if pick.get('media_type') == 'tv':
        return redirect(f"/series/{pick['id']}/")
    return redirect(f"/movies/{pick['id']}/")

def genres_view(request):
    client = TMDBClient()
    genres = client.get_genres_list()
    return render(request, 'catalog/genres.html', {'genres': genres})

def person_detail(request, person_id):
    client = TMDBClient()
    person = client.get_person(person_id)
    credits = person.get('combined_credits', {}).get('cast', [])
    
    # Sort credits by popularity or vote_count
    credits = sorted(credits, key=lambda x: x.get('vote_count', 0), reverse=True)[:24]
    for c in credits:
        c['display_title'] = c.get('title') or c.get('name') or 'Unknown Title'
        c['media_type'] = c.get('media_type', 'movie')
        client._attach_age_rating(c, c['media_type'])

    user_saved_ids = set()
    if request.user.is_authenticated:
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user).values_list('tmdb_id', flat=True))

    return render(request, 'catalog/person_detail.html', {
        'person': person,
        'credits': credits,
        'user_saved_ids': user_saved_ids
    })


