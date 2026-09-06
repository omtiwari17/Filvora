import re
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from apps.tmdb.client import TMDBClient
from apps.library.models import LibraryItem
from apps.watch.models import UserRating

def get_pagination_context(page, total_pages=500):
    try:
        current = max(1, int(page or 1))
    except (ValueError, TypeError):
        current = 1
    
    total_pages = max(1, int(total_pages or 1))
    if current > total_pages:
        current = total_pages

    if total_pages <= 1:
        return {
            'current_page': 1,
            'total_pages': 1,
            'has_prev': False,
            'prev_page': 1,
            'has_next': False,
            'next_page': 1,
            'page_numbers': [],
        }

    start_p = max(1, current - 2)
    end_p = min(total_pages, current + 2)
    page_numbers = list(range(start_p, end_p + 1))
    return {
        'current_page': current,
        'total_pages': total_pages,
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
    explicit_sort = request.GET.get('sort')
    audience = request.GET.get('audience', 'all')
    page = request.GET.get('page', '1')
    kids_mode = is_kids_profile(request)

    if explicit_sort:
        sort_by = explicit_sort
    elif category == 'top_rated':
        sort_by = 'vote_average.desc'
    else:
        sort_by = 'popularity.desc'

    movies = client.get_movies_catalog(
        category=category,
        genre_id=genre_id,
        sort_by=sort_by,
        page=page,
        kids_only=kids_mode,
        audience=audience
    )
    genres = client.get_genres_list('movie')

    user_saved_ids = set()
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))

    pagination = get_pagination_context(page)

    return render(request, 'catalog/movie_browse.html', {
        'movies': movies,
        'genres': genres,
        'selected_category': category,
        'selected_genre': genre_id,
        'selected_sort': sort_by,
        'selected_audience': audience,
        'pagination': pagination,
        'user_saved_ids': user_saved_ids
    })

def movie_detail(request, tmdb_id):
    client = TMDBClient()
    movie = client.get_movie_details(tmdb_id)
    movie['display_title'] = movie.get('title', f"Movie {tmdb_id}")

    # Check if movie is saved in user's library for active profile
    in_library = False
    user_saved_ids = set()
    profile = None
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))
        in_library = int(tmdb_id) in user_saved_ids

    cast = []
    directors = []
    if 'credits' in movie:
        if 'cast' in movie['credits']:
            cast = movie['credits']['cast'][:16]
        if 'crew' in movie['credits']:
            directors = [c for c in movie['credits']['crew'] if c.get('job') == 'Director']

    recommendations = []
    if 'recommendations' in movie and 'results' in movie['recommendations']:
        recommendations = movie['recommendations']['results'][:10]

    # Get user's existing rating for this movie
    user_rating = 0
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        rating_obj = UserRating.objects.filter(
            user=request.user, profile=profile, tmdb_id=tmdb_id, media_type='movie'
        ).first()
        if rating_obj:
            user_rating = rating_obj.score

    # Fetch official franchise saga collection if movie belongs to a collection
    collection = None
    belongs_to = movie.get('belongs_to_collection')
    if belongs_to and isinstance(belongs_to, dict) and belongs_to.get('id'):
        collection = client.get_collection(belongs_to.get('id'))
        if collection and 'parts' in collection:
            curr_id = int(tmdb_id)
            curr_order = None
            for part in collection['parts']:
                if part.get('id') == curr_id:
                    part['is_current'] = True
                    curr_order = part.get('franchise_order', 1)
                else:
                    part['is_current'] = False
            
            collection['current_chapter_num'] = curr_order or 1
            for part in collection['parts']:
                p_order = part.get('franchise_order', 1)
                if part['is_current']:
                    part['saga_relation'] = 'Now Viewing'
                elif curr_order and p_order < curr_order:
                    part['saga_relation'] = 'Prequel'
                elif curr_order and p_order > curr_order:
                    part['saga_relation'] = 'Sequel'
                else:
                    part['saga_relation'] = f"Chapter {p_order}"

    return render(request, 'catalog/movie_detail.html', {
        'movie': movie,
        'in_library': in_library,
        'user_saved_ids': user_saved_ids,
        'cast': cast,
        'directors': directors,
        'recommendations': recommendations,
        'collection': collection,
        'user_rating': user_rating,
        'trailer_key': movie.get('trailer_key'),
        'star_range': [1, 2, 3, 4, 5],
    })

def series_browse(request):
    client = TMDBClient()
    category = request.GET.get('category', 'popular')
    genre_id = request.GET.get('genre')
    explicit_sort = request.GET.get('sort')
    audience = request.GET.get('audience', 'all')
    page = request.GET.get('page', '1')
    kids_mode = is_kids_profile(request)

    if explicit_sort:
        sort_by = explicit_sort
    elif category == 'top_rated':
        sort_by = 'vote_average.desc'
    else:
        sort_by = 'popularity.desc'

    series_list = client.get_series_catalog(
        category=category,
        genre_id=genre_id,
        sort_by=sort_by,
        page=page,
        kids_only=kids_mode,
        audience=audience
    )
    genres = client.get_genres_list('tv')

    user_saved_ids = set()
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))

    pagination = get_pagination_context(page)

    return render(request, 'catalog/series_browse.html', {
        'series_list': series_list,
        'genres': genres,
        'selected_category': category,
        'selected_genre': genre_id,
        'selected_sort': sort_by,
        'selected_audience': audience,
        'pagination': pagination,
        'user_saved_ids': user_saved_ids
    })


def format_season_runtime(minutes: int) -> str:
    """Format total minutes into human-readable duration (e.g. '6h 38m')."""
    if not minutes:
        return ""
    hrs = minutes // 60
    mins = minutes % 60
    if hrs > 0 and mins > 0:
        return f"{hrs}h {mins}m"
    elif hrs > 0:
        return f"{hrs} hrs"
    return f"{mins}m"


def get_series_season_partitions(series: dict, chunk_size: int = 100) -> list:
    """
    Extracts and organizes seasons for a TV series.
    For standard series (e.g. Breaking Bad, Stranger Things), returns the official TMDB seasons.
    For mega-seasons (e.g. Taarak Mehta Ka Ooltah Chashmah, daily soaps, or continuous anime where
    a single season has > 100 episodes), automatically partitions the massive episode catalog into
    clean, manageable seasons/volumes of 100 episodes (matching SonyLIV/official platform streaming seasons).
    """
    raw_seasons = [s for s in series.get('seasons', []) if s.get('season_number', 0) > 0]
    if not raw_seasons:
        num_seasons = series.get('number_of_seasons', 1) or 1
        return [{
            'partition_id': i,
            'season_number': i,
            'tmdb_season_number': i,
            'name': f"Season {i}",
            'range_label': '',
            'start_episode': 1,
            'end_episode': 10,
            'episode_count': 10,
            'is_chunked': False,
        } for i in range(1, num_seasons + 1)]

    # Case 1: Exactly 1 season with > 100 episodes (e.g. Taarak Mehta Ka Ooltah Chashmah with 4,800+ episodes)
    if len(raw_seasons) == 1 and raw_seasons[0].get('episode_count', 0) > chunk_size:
        s0 = raw_seasons[0]
        total_eps = s0.get('episode_count', 0)
        tmdb_s = s0.get('season_number', 1)
        partitions = []
        part_idx = 1
        for start_ep in range(1, total_eps + 1, chunk_size):
            end_ep = min(start_ep + chunk_size - 1, total_eps)
            count = end_ep - start_ep + 1
            partitions.append({
                'partition_id': part_idx,
                'season_number': part_idx,
                'tmdb_season_number': tmdb_s,
                'name': f"Season {part_idx}",
                'range_label': f"Eps {start_ep}–{end_ep}",
                'start_episode': start_ep,
                'end_episode': end_ep,
                'episode_count': count,
                'is_chunked': True,
                'poster_path': s0.get('poster_path', ''),
            })
            part_idx += 1
        return partitions

    # Case 2: General series (standard seasons or multi-season shows)
    partitions = []
    for s in raw_seasons:
        s_num = s.get('season_number', 1)
        ep_count = s.get('episode_count', 0)
        if ep_count > chunk_size:
            part_idx = 1
            for start_ep in range(1, ep_count + 1, chunk_size):
                end_ep = min(start_ep + chunk_size - 1, ep_count)
                count = end_ep - start_ep + 1
                pid = int(f"{s_num}{part_idx:02d}")
                partitions.append({
                    'partition_id': pid,
                    'season_number': s_num,
                    'tmdb_season_number': s_num,
                    'name': f"Season {s_num} (Part {part_idx})",
                    'range_label': f"Eps {start_ep}–{end_ep}",
                    'start_episode': start_ep,
                    'end_episode': end_ep,
                    'episode_count': count,
                    'is_chunked': True,
                    'poster_path': s.get('poster_path', ''),
                })
                part_idx += 1
        else:
            partitions.append({
                'partition_id': s_num,
                'season_number': s_num,
                'tmdb_season_number': s_num,
                'name': s.get('name') or f"Season {s_num}",
                'range_label': '',
                'start_episode': 1,
                'end_episode': ep_count,
                'episode_count': ep_count,
                'is_chunked': False,
                'poster_path': s.get('poster_path', ''),
            })

    return partitions


def series_detail(request, tmdb_id):
    client = TMDBClient()
    series = client.get_tv_details(tmdb_id)
    series['display_title'] = series.get('name', f"Series {tmdb_id}")

    in_library = False
    profile = None
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        in_library = LibraryItem.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type='tv'
        ).exists()

    cast = []
    creators = series.get('created_by', [])
    if 'credits' in series and 'cast' in series['credits']:
        cast = series['credits']['cast'][:16]

    # Partition seasons (breaks mega-seasons like TMKOC into clean 100-episode seasons)
    seasons = get_series_season_partitions(series)
    avg_runtime = series.get('episode_run_time', [45])[0] if series.get('episode_run_time') else 45

    # Cache TMDB season data in a dict to avoid redundant fetches
    loaded_tmdb_seasons = {}
    for s in seasons:
        tmdb_s = s.get('tmdb_season_number', 1)
        if tmdb_s not in loaded_tmdb_seasons:
            loaded_tmdb_seasons[tmdb_s] = client.get_tv_season(tmdb_id, tmdb_s).get('episodes', [])
        
        all_s_eps = loaded_tmdb_seasons[tmdb_s]
        if s.get('is_chunked'):
            start_i = s['start_episode'] - 1
            end_i = s['end_episode']
            part_eps = all_s_eps[start_i:end_i]
        else:
            part_eps = all_s_eps

        s_total_mins = sum(e.get('runtime') or avg_runtime for e in part_eps)
        if not s_total_mins and s.get('episode_count'):
            s_total_mins = s.get('episode_count', 0) * avg_runtime

        s['total_minutes'] = s_total_mins
        s['total_hours_formatted'] = format_season_runtime(s_total_mins)
        s['total_hours_decimal'] = f"{round(s_total_mins / 60.0, 1)} hrs" if s_total_mins else ""

    # Compute season-wise watch time if user is logged in
    if request.user.is_authenticated:
        from apps.watch.models import WatchProgress
        user_progress = WatchProgress.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type='tv'
        )
        season_stats = {}
        for p in user_progress:
            s_num = p.season or 1
            if s_num not in season_stats:
                season_stats[s_num] = 0
            season_stats[s_num] += p.position_seconds

        for s in seasons:
            s_num = s.get('season_number', 1)
            sec = season_stats.get(s_num, 0)
            if sec >= 3600:
                s['play_time_formatted'] = f"{round(sec / 3600.0, 1)} hrs"
            elif sec >= 60:
                s['play_time_formatted'] = f"{int(sec // 60)} mins"
            elif sec > 0:
                s['play_time_formatted'] = f"{int(sec)}s"
            else:
                s['play_time_formatted'] = None

    initial_partition = seasons[0] if seasons else None
    initial_season_num = initial_partition['partition_id'] if initial_partition else 1
    tmdb_initial_s = initial_partition.get('tmdb_season_number', 1) if initial_partition else 1

    all_init_eps = loaded_tmdb_seasons.get(tmdb_initial_s, [])
    if initial_partition and initial_partition.get('is_chunked'):
        episodes = all_init_eps[initial_partition['start_episode'] - 1 : initial_partition['end_episode']]
    else:
        episodes = all_init_eps

    initial_season_runtime = initial_partition.get('total_hours_formatted', '') if initial_partition else ''
    initial_season_decimal = initial_partition.get('total_hours_decimal', '') if initial_partition else ''

    # Get user's existing rating for this series
    user_rating = 0
    if request.user.is_authenticated:
        rating_obj = UserRating.objects.filter(
            user=request.user, profile=profile, tmdb_id=tmdb_id, media_type='tv'
        ).first()
        if rating_obj:
            user_rating = rating_obj.score

    recommendations = []
    if 'recommendations' in series and 'results' in series['recommendations']:
        recommendations = series['recommendations']['results'][:10]

    return render(request, 'catalog/series_detail.html', {
        'series': series,
        'in_library': in_library,
        'cast': cast,
        'creators': creators,
        'seasons': seasons,
        'current_season': initial_season_num,
        'current_partition': initial_partition,
        'episodes': episodes,
        'initial_season_runtime': initial_season_runtime,
        'initial_season_decimal': initial_season_decimal,
        'recommendations': recommendations,
        'user_rating': user_rating,
        'trailer_key': series.get('trailer_key'),
        'star_range': [1, 2, 3, 4, 5],
    })


def trailer_api(request, media_type, tmdb_id):
    """API endpoint to dynamically fetch the official YouTube trailer key for any title."""
    client = TMDBClient()
    trailer_key = client.get_official_trailer(tmdb_id, media_type)
    return JsonResponse({'trailer_key': trailer_key, 'tmdb_id': tmdb_id, 'media_type': media_type})


def season_episodes(request, tmdb_id, season_number):
    client = TMDBClient()
    series = client.get_tv_details(tmdb_id)
    seasons = get_series_season_partitions(series)

    target_partition = None
    target_num = int(season_number) if str(season_number).isdigit() else 1
    for s in seasons:
        if s.get('partition_id') == target_num:
            target_partition = s
            break

    if not target_partition:
        for s in seasons:
            if s.get('season_number') == target_num:
                target_partition = s
                break

    if not target_partition and seasons:
        target_partition = seasons[0]

    if target_partition:
        real_tmdb_s = target_partition.get('tmdb_season_number', 1)
        season_data = client.get_tv_season(tmdb_id, real_tmdb_s)
        all_eps = season_data.get('episodes', [])

        if target_partition.get('is_chunked'):
            start_i = target_partition['start_episode'] - 1
            end_i = target_partition['end_episode']
            episodes = all_eps[start_i:end_i]
        else:
            episodes = all_eps

        disp_season_num = target_partition['partition_id']
    else:
        disp_season_num = target_num
        season_data = client.get_tv_season(tmdb_id, disp_season_num)
        episodes = season_data.get('episodes', [])

    avg_runtime = series.get('episode_run_time', [45])[0] if series.get('episode_run_time') else 45
    total_mins = sum(ep.get('runtime') or avg_runtime for ep in episodes)
    total_formatted = format_season_runtime(total_mins)

    return render(request, 'catalog/partials/episode_list.html', {
        'tmdb_id': tmdb_id,
        'season_number': disp_season_num,
        'partition': target_partition,
        'episodes': episodes,
        'season_total_runtime': total_formatted,
        'season_total_hours_decimal': f"{round(total_mins / 60.0, 1)} hrs" if total_mins else "",
        'season_total_minutes': total_mins,
    })

KNOWN_RATINGS = {'G', 'PG', 'PG-13', 'R', 'NC-17', '18+', 'TV-MA', 'TV-14', 'TV-PG', 'TV-G', 'TV-Y7', 'TV-Y'}

def parse_search_query(raw_q, explicit_rating=None):
    raw_q = (raw_q or '').strip()
    rating = (explicit_rating or '').strip().upper()
    clean_q = raw_q

    # Check for formats like "rating:PG-13", "cert:R", "t=rating", "rating=R", "cert=PG-13", "rate:18+", "t=R"
    match = re.search(r'(?:rating|cert|rate|t)[=:]([a-zA-Z0-9\-+]+)', clean_q, re.IGNORECASE)
    if match:
        found_rating = match.group(1).upper()
        if found_rating in KNOWN_RATINGS or found_rating in ['R', 'PG13', 'TVMA', 'TV14', 'PG', 'G', '18+']:
            if found_rating == 'PG13': found_rating = 'PG-13'
            elif found_rating == 'TVMA': found_rating = 'TV-MA'
            elif found_rating == 'TV14': found_rating = 'TV-14'
            rating = found_rating
        clean_q = re.sub(r'(?:rating|cert|rate|t)[=:][a-zA-Z0-9\-+]+', '', clean_q, flags=re.IGNORECASE).strip()

    # Check if query itself is an age rating (e.g. "PG-13", "R", "TV-MA", "18+", "PG", "G")
    upper_q = clean_q.upper()
    if upper_q in KNOWN_RATINGS or upper_q in ['PG13', 'TVMA', 'TV14', 'R-RATED', 'ADULT']:
        if upper_q in ['PG13', 'PG-13']: rating = 'PG-13'
        elif upper_q in ['TVMA', 'TV-MA']: rating = 'TV-MA'
        elif upper_q in ['TV14', 'TV-14']: rating = 'TV-14'
        elif upper_q in ['R', 'R-RATED']: rating = 'R'
        elif upper_q in ['18+', 'ADULT']: rating = '18+'
        elif upper_q in ['PG', 'G', 'NC-17', 'TV-PG', 'TV-G', 'TV-Y7', 'TV-Y']: rating = upper_q
        clean_q = ''
    elif not rating and len(clean_q.split()) > 1:
        # Check if the last word in a multi-word search is a rating code (e.g. "Batman PG-13", "Deadpool R")
        words = clean_q.split()
        last_word = words[-1].upper()
        if last_word in KNOWN_RATINGS:
            rating = last_word
            clean_q = " ".join(words[:-1]).strip()

    return clean_q, rating

def search_suggest(request):
    raw_q = request.GET.get('q', '').strip()
    explicit_rating = request.GET.get('rating') or request.GET.get('cert')
    clean_q, rating_filter = parse_search_query(raw_q, explicit_rating)

    client = TMDBClient()
    
    if clean_q and len(clean_q) >= 2:
        categorized = client.search_categorized(clean_q)
        if rating_filter:
            categorized['movies'] = [m for m in categorized['movies'] if m.get('age_rating', '').upper() == rating_filter or rating_filter in m.get('age_rating', '').upper()]
            categorized['series'] = [s for s in categorized['series'] if s.get('age_rating', '').upper() == rating_filter or rating_filter in s.get('age_rating', '').upper()]
    elif rating_filter:
        movies = client.discover_content(media_type='movie', certification=rating_filter)[:4]
        series = client.discover_content(media_type='tv', certification=rating_filter)[:4]
        categorized = {'movies': movies, 'series': series, 'people': []}
    else:
        categorized = {'movies': [], 'series': [], 'people': []}

    return render(request, 'catalog/partials/search_suggestions.html', {
        'categorized': categorized,
        'movies': categorized['movies'][:4],
        'series': categorized['series'][:4],
        'people': categorized['people'][:3],
        'has_results': bool(categorized['movies'] or categorized['series'] or categorized['people']),
        'query': raw_q,
    })

def search_results(request):
    raw_q = request.GET.get('q', '').strip()
    page = request.GET.get('page', '1')
    explicit_rating = request.GET.get('rating') or request.GET.get('cert')
    clean_q, rating_filter = parse_search_query(raw_q, explicit_rating)

    client = TMDBClient()
    results = []

    try:
        p_num = max(1, int(page))
    except (ValueError, TypeError):
        p_num = 1

    total_pages = 1

    if clean_q:
        search_data = client.search_multi_paginated(clean_q, page=p_num)
        results = search_data['results']
        total_pages = search_data.get('total_pages', 1)

        if rating_filter:
            results = [r for r in results if r.get('age_rating', '').upper() == rating_filter or rating_filter in r.get('age_rating', '').upper()]
            total_pages = 1 if len(results) < 20 else total_pages
    elif rating_filter:
        movie_results = client.discover_content(media_type='movie', certification=rating_filter, page=p_num)
        tv_results = client.discover_content(media_type='tv', certification=rating_filter, page=p_num)
        results = movie_results + tv_results
        total_pages = 1 if len(results) < 20 else 5

    user_saved_ids = set()
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))

    pagination = get_pagination_context(page, total_pages=total_pages)

    return render(request, 'catalog/search_results.html', {
        'results': results,
        'query': raw_q,
        'clean_query': clean_q,
        'selected_rating': rating_filter,
        'pagination': pagination,
        'user_saved_ids': user_saved_ids,
    })

def is_kids_profile(request):
    if not request.user.is_authenticated:
        return False
    from apps.accounts.utils import get_active_profile
    p = get_active_profile(request)
    return bool(p and p.is_kids)

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
    page = request.GET.get('page', '1')
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
        sort_by=sort_by,
        page=page
    )

    genres = client.get_genres_list(media_type)
    user_saved_ids = set()
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))

    total_pages = 1 if len(results) < 24 and str(page).strip() in ['1', ''] else 500
    pagination = get_pagination_context(page, total_pages=total_pages)

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
        'pagination': pagination,
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
    active_type = request.GET.get('type', 'movie')
    if active_type not in ['movie', 'tv']:
        active_type = 'movie'
    movie_genres = client.get_genres_list('movie')
    tv_genres = client.get_genres_list('tv')
    return render(request, 'catalog/genres.html', {
        'movie_genres': movie_genres,
        'tv_genres': tv_genres,
        'active_type': active_type,
        'genres': movie_genres if active_type == 'movie' else tv_genres,
    })

def person_detail(request, person_id):
    client = TMDBClient()
    person = client.get_person(person_id)
    combined = person.get('combined_credits', {})
    cast_credits = combined.get('cast', [])
    crew_credits = combined.get('crew', [])
    
    # Combine cast and crew credits, removing duplicate IDs
    all_credits = []
    seen_ids = set()
    for c in (crew_credits + cast_credits):
        cid = c.get('id')
        if cid and cid not in seen_ids:
            seen_ids.add(cid)
            c['display_title'] = c.get('title') or c.get('name') or 'Unknown Title'
            c['title'] = c['display_title']
            c['name'] = c['display_title']
            c['media_type'] = c.get('media_type', 'movie')
            client._attach_age_rating(c, c['media_type'])
            all_credits.append(c)

    # Sort credits by vote_count and popularity
    credits = sorted(all_credits, key=lambda x: (x.get('vote_count', 0), x.get('popularity', 0)), reverse=True)[:24]

    user_saved_ids = set()
    if request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        user_saved_ids = set(LibraryItem.objects.filter(user=request.user, profile=profile).values_list('tmdb_id', flat=True))

    return render(request, 'catalog/person_detail.html', {
        'person': person,
        'credits': credits,
        'user_saved_ids': user_saved_ids
    })


