import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import WatchProgress, UserRating
from apps.accounts.utils import get_active_profile



@csrf_exempt
@login_required
def save_progress(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        position_seconds = float(data.get('position', 0))
        duration_seconds = float(data.get('duration', 0))
        season = int(data.get('season')) if data.get('season') else None
        episode = int(data.get('episode')) if data.get('episode') else None

        # Determine if video is completed (e.g. >90% watched or <=30s remaining)
        completed = False
        if duration_seconds > 0:
            if position_seconds >= (duration_seconds * 0.9) or (duration_seconds - position_seconds) <= 30:
                completed = True

        # Ignore negligible positions (< 15s) that occur during page load or failed streams
        if position_seconds < 15 and not completed:
            return JsonResponse({'status': 'ignored', 'message': 'Position below threshold'})

        profile = get_active_profile(request)

        progress, _ = WatchProgress.objects.update_or_create(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type,
            season=season,
            episode=episode,
            defaults={
                'position_seconds': position_seconds,
                'duration_seconds': duration_seconds,
                'completed': completed,
            }
        )

        return JsonResponse({
            'status': 'ok',
            'completed': completed,
            'progress_percentage': progress.progress_percentage
        })
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


from datetime import datetime, timezone, timedelta
from django.shortcuts import render, redirect
from apps.tmdb.client import TMDBClient

def format_time_str(seconds: float) -> str:
    secs = int(seconds or 0)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    remaining_seconds = secs % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes:02d}:{remaining_seconds:02d}"

@login_required
def history_view(request):
    client = TMDBClient()
    profile = get_active_profile(request)
    items = WatchProgress.objects.filter(user=request.user, profile=profile).order_by('-updated_at')
    
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)

    grouped_history = {
        'Today': [],
        'Yesterday': [],
        'This Week': [],
        'Earlier': []
    }

    # Pre-fetch user ratings for active profile for quick lookup
    user_ratings = {}
    rated_items_records = list(UserRating.objects.filter(user=request.user, profile=profile).order_by('-updated_at'))
    for r in rated_items_records:
        user_ratings[(r.tmdb_id, r.media_type)] = r.score

    for p in items:
        item_date = p.updated_at.date()
        if p.media_type == 'movie':
            data = dict(client.get_movie(p.tmdb_id))
            data['display_title'] = data.get('title', f"Movie {p.tmdb_id}")
            data['sub_label'] = "Movie"
            data['watch_url'] = f"/watch/movie/{p.tmdb_id}/"
        else:
            data = dict(client.get_tv(p.tmdb_id))
            s_num = p.season or 1
            ep_num = p.episode or 1
            data['display_title'] = data.get('name', f"Series {p.tmdb_id}")
            data['sub_label'] = f"S{s_num:02d}E{ep_num:02d}"
            data['watch_url'] = f"/watch/tv/{p.tmdb_id}/{s_num}/{ep_num}/"

        data['id'] = p.tmdb_id
        data['media_type'] = p.media_type
        data['position_formatted'] = format_time_str(p.position_seconds)
        data['duration_formatted'] = format_time_str(p.duration_seconds)
        data['progress_percentage'] = p.progress_percentage
        data['completed'] = p.completed
        data['updated_at'] = p.updated_at
        data['rating_score'] = user_ratings.get((p.tmdb_id, p.media_type), 0)

        if item_date == today:
            grouped_history['Today'].append(data)
        elif item_date == yesterday:
            grouped_history['Yesterday'].append(data)
        elif item_date >= seven_days_ago:
            grouped_history['This Week'].append(data)
        else:
            grouped_history['Earlier'].append(data)

    # Build standalone Rated Titles list (including unstreamed titles that were rated)
    rated_titles = []
    for r in rated_items_records:
        if r.media_type == 'movie':
            r_data = dict(client.get_movie(r.tmdb_id))
            r_data['display_title'] = r_data.get('title', f"Movie {r.tmdb_id}")
            r_data['sub_label'] = "Movie"
            r_data['watch_url'] = f"/watch/movie/{r.tmdb_id}/"
            r_data['detail_url'] = f"/movies/{r.tmdb_id}/"
        else:
            r_data = dict(client.get_tv(r.tmdb_id))
            r_data['display_title'] = r_data.get('name', f"Series {r.tmdb_id}")
            r_data['sub_label'] = "TV Series"
            r_data['watch_url'] = f"/watch/tv/{r.tmdb_id}/1/1/"
            r_data['detail_url'] = f"/series/{r.tmdb_id}/"

        r_data['id'] = r.tmdb_id
        r_data['media_type'] = r.media_type
        r_data['rating_score'] = r.score
        r_data['rated_at'] = r.updated_at
        rated_titles.append(r_data)

    # Filter out empty date groups
    active_groups = {k: v for k, v in grouped_history.items() if v}

    return render(request, 'watch/history.html', {
        'grouped_history': active_groups,
        'total_items': len(items),
        'rated_titles': rated_titles,
        'total_rated': len(rated_titles),
        'star_range': [1, 2, 3, 4, 5],
    })

@csrf_exempt
@login_required
def remove_progress(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        profile = get_active_profile(request)

        WatchProgress.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type
        ).delete()

        if request.headers.get('HX-Request'):
            from django.http import HttpResponse
            return HttpResponse("", status=200)

        return JsonResponse({'status': 'ok', 'message': 'Removed from continue watching'})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def clear_history(request):
    if request.method == 'POST':
        profile = get_active_profile(request)
        WatchProgress.objects.filter(user=request.user, profile=profile).delete()
    return redirect('/watch/history/')


@csrf_exempt
@login_required
def rate_content(request):
    """HTMX endpoint: create or update a user rating (1-5 stars) for active profile."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        score = int(data.get('score', 0))

        if score < 1 or score > 5:
            return JsonResponse({'status': 'error', 'message': 'Score must be 1-5'}, status=400)

        profile = get_active_profile(request)

        rating, created = UserRating.objects.update_or_create(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type,
            defaults={'score': score}
        )

        # Return HTMX partial: re-render the star widget with the new score
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            html = render_to_string('components/rating_stars.html', {
                'rating_score': score,
                'tmdb_id': tmdb_id,
                'media_type': media_type,
                'star_range': [1, 2, 3, 4, 5],
            })
            from django.http import HttpResponse
            return HttpResponse(html)

        return JsonResponse({
            'status': 'ok',
            'score': score,
            'created': created,
        })
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@login_required
def remove_rating(request):
    """HTMX endpoint: delete a user rating for active profile."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        profile = get_active_profile(request)

        UserRating.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type
        ).delete()

        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            html = render_to_string('components/rating_stars.html', {
                'rating_score': 0,
                'tmdb_id': tmdb_id,
                'media_type': media_type,
                'star_range': [1, 2, 3, 4, 5],
            })
            from django.http import HttpResponse
            return HttpResponse(html)

        return JsonResponse({'status': 'ok', 'message': 'Rating removed'})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)



@login_required
def analytics_view(request):
    from collections import Counter
    client = TMDBClient()
    profile = get_active_profile(request)
    items = list(WatchProgress.objects.filter(user=request.user, profile=profile).order_by('-updated_at'))
    
    total_seconds = sum(p.position_seconds for p in items)
    total_hours = round(total_seconds / 3600.0, 1)
    
    movie_items = [p for p in items if p.media_type == 'movie']
    tv_items = [p for p in items if p.media_type == 'tv']
    completed_items = [p for p in items if p.completed]
    
    total_movies = len(set(p.tmdb_id for p in movie_items))
    total_episodes = len(tv_items)
    
    # Genre calculations
    genre_counter = Counter()
    for p in items[:25]:
        if p.media_type == 'movie':
            details = client.get_movie_details(p.tmdb_id)
        else:
            details = client.get_tv_details(p.tmdb_id)
        for g in details.get('genres', []):
            gname = g.get('name') if isinstance(g, dict) else str(g)
            if gname:
                genre_counter[gname] += 1

    total_genre_hits = sum(genre_counter.values()) or 1
    top_genres = []
    for gname, count in genre_counter.most_common(5):
        top_genres.append({
            'name': gname,
            'count': count,
            'percentage': int((count / total_genre_hits) * 100)
        })

    favorite_genre = top_genres[0]['name'] if top_genres else "Cinematic Variety"

    # Season-wise play time breakdown for TV series
    series_season_breakdown = {}
    for p in tv_items:
        series_id = p.tmdb_id
        season_num = p.season or 1
        if series_id not in series_season_breakdown:
            series_season_breakdown[series_id] = {
                'id': series_id,
                'title': '',
                'total_seconds': 0,
                'total_episodes': 0,
                'seasons': {}
            }
        
        series_season_breakdown[series_id]['total_seconds'] += p.position_seconds
        series_season_breakdown[series_id]['total_episodes'] += 1

        if season_num not in series_season_breakdown[series_id]['seasons']:
            series_season_breakdown[series_id]['seasons'][season_num] = {
                'season_number': season_num,
                'total_seconds': 0,
                'episodes_count': 0,
                'completed_count': 0,
            }
        
        s_data = series_season_breakdown[series_id]['seasons'][season_num]
        s_data['total_seconds'] += p.position_seconds
        s_data['episodes_count'] += 1
        if p.completed:
            s_data['completed_count'] += 1

    series_season_list = []
    for s_id, s_info in series_season_breakdown.items():
        tv_details = client.get_tv(s_id)
        s_info['title'] = tv_details.get('name') or tv_details.get('title') or f"Series {s_id}"
        s_info['poster_path'] = tv_details.get('poster_path')
        s_info['total_hours'] = round(s_info['total_seconds'] / 3600.0, 1)
        s_info['total_hours_formatted'] = f"{s_info['total_hours']} hrs" if s_info['total_hours'] >= 1.0 else f"{max(1, int(s_info['total_seconds'] // 60))} mins"
        
        formatted_seasons = []
        for s_num in sorted(s_info['seasons'].keys()):
            s_data = s_info['seasons'][s_num]
            hrs = round(s_data['total_seconds'] / 3600.0, 1)
            mins = int((s_data['total_seconds'] % 3600) // 60)
            if hrs >= 1.0:
                play_time_str = f"{hrs} hrs"
            elif s_data['total_seconds'] >= 60:
                play_time_str = f"{mins} mins"
            else:
                play_time_str = f"{int(s_data['total_seconds'])}s"
            
            formatted_seasons.append({
                'season_number': s_num,
                'play_time_str': play_time_str,
                'play_time_hours': hrs,
                'episodes_watched': s_data['episodes_count'],
                'episodes_completed': s_data['completed_count'],
            })
        
        s_info['formatted_seasons'] = formatted_seasons
        series_season_list.append(s_info)
    
    series_season_list.sort(key=lambda x: x['total_seconds'], reverse=True)

    # Most watched item
    most_watched_title = "None yet"
    if items:
        longest_p = max(items, key=lambda x: x.position_seconds)
        if longest_p.media_type == 'movie':
            data = client.get_movie(longest_p.tmdb_id)
            most_watched_title = data.get('title', f"Movie {longest_p.tmdb_id}")
        else:
            data = client.get_tv(longest_p.tmdb_id)
            most_watched_title = data.get('name', f"Series {longest_p.tmdb_id}")

    # User rating stats
    all_ratings = list(UserRating.objects.filter(user=request.user, profile=profile).values_list('score', flat=True))
    total_ratings = len(all_ratings)
    avg_rating = round(sum(all_ratings) / total_ratings, 1) if total_ratings > 0 else 0

    return render(request, 'watch/analytics.html', {
        'total_hours': total_hours,
        'total_movies': total_movies,
        'total_episodes': total_episodes,
        'completed_count': len(completed_items),
        'top_genres': top_genres,
        'favorite_genre': favorite_genre,
        'most_watched_title': most_watched_title,
        'total_titles': len(items),
        'series_season_list': series_season_list,
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
    })


