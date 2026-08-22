from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.tmdb.client import TMDBClient

from apps.watch.models import WatchProgress

@login_required
def watch(request, media_type, tmdb_id, season=None, episode=None):
    client = TMDBClient()
    if media_type == 'movie':
        media = client.get_movie(tmdb_id)
        title = media.get('title', 'Unknown Movie')
    else:
        media = client.get_tv(tmdb_id)
        series_name = media.get('name', 'Unknown Series')
        if season and episode:
            title = f"{series_name} — S{season}:E{episode}"
        else:
            title = series_name
        
    # Standard open-source Big Buck Bunny HLS stream for testing
    video_url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    
    # Check if user has saved watch progress to resume
    resume_position = 0
    progress = WatchProgress.objects.filter(
        user=request.user,
        tmdb_id=tmdb_id,
        media_type=media_type,
        season=season,
        episode=episode
    ).first()
    
    if progress and not progress.completed and progress.position_seconds > 5:
        resume_position = round(progress.position_seconds, 1)

    return render(request, 'playback/watch.html', {
        'media': media,
        'title': title,
        'video_url': video_url,
        'media_type': media_type,
        'tmdb_id': tmdb_id,
        'season': season or '',
        'episode': episode or '',
        'resume_position': resume_position,
    })
