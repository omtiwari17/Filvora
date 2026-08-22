import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import WatchProgress

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
