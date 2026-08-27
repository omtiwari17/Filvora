import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import WatchProgress

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

        progress, _ = WatchProgress.objects.update_or_create(
            user=request.user,
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
    items = WatchProgress.objects.filter(user=request.user).order_by('-updated_at')
    
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

        if item_date == today:
            grouped_history['Today'].append(data)
        elif item_date == yesterday:
            grouped_history['Yesterday'].append(data)
        elif item_date >= seven_days_ago:
            grouped_history['This Week'].append(data)
        else:
            grouped_history['Earlier'].append(data)

    # Filter out empty date groups
    active_groups = {k: v for k, v in grouped_history.items() if v}

    return render(request, 'watch/history.html', {
        'grouped_history': active_groups,
        'total_items': len(items)
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

        WatchProgress.objects.filter(
            user=request.user,
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
        WatchProgress.objects.filter(user=request.user).delete()
    return redirect('/watch/history/')

@login_required
def analytics_view(request):
    from collections import Counter
    client = TMDBClient()
    items = list(WatchProgress.objects.filter(user=request.user).order_by('-updated_at'))
    
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

    return render(request, 'watch/analytics.html', {
        'total_hours': total_hours,
        'total_movies': total_movies,
        'total_episodes': total_episodes,
        'completed_count': len(completed_items),
        'top_genres': top_genres,
        'favorite_genre': favorite_genre,
        'most_watched_title': most_watched_title,
        'total_titles': len(items)
    })


