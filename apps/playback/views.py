from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.tmdb.client import TMDBClient

from apps.watch.models import WatchProgress

from apps.playback.providers import PROVIDERS, get_provider

@login_required
def watch(request, media_type, tmdb_id, season=None, episode=None):
    client = TMDBClient()
    server_id = request.GET.get('server')
    provider = get_provider(server_id)

    if media_type == 'movie':
        media = client.get_movie(tmdb_id)
        title = media.get('title', 'Unknown Movie')
        video_url = provider.get_movie_url(tmdb_id)
        next_episode = None
    else:
        media = client.get_tv(tmdb_id)
        series_name = media.get('name', 'Unknown Series')
        s_num = season or 1
        ep_num = episode or 1
        title = f"{series_name} — S{s_num}:E{ep_num}"
        video_url = provider.get_tv_url(tmdb_id, s_num, ep_num)
        
        # Calculate next episode
        next_episode = {
            'season': s_num,
            'episode': ep_num + 1,
            'url': f"/watch/tv/{tmdb_id}/{s_num}/{ep_num + 1}/"
        }
    
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
        'season': season or (1 if media_type == 'tv' else ''),
        'episode': episode or (1 if media_type == 'tv' else ''),
        'resume_position': resume_position,
        'providers': PROVIDERS,
        'current_server': provider.id,
        'next_episode': next_episode,
    })
