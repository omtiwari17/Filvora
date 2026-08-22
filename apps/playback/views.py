from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.tmdb.client import TMDBClient

@login_required
def watch(request, media_type, tmdb_id):
    client = TMDBClient()
    if media_type == 'movie':
        media = client.get_movie(tmdb_id)
        title = media.get('title', 'Unknown Movie')
    else:
        media = client.get_tv(tmdb_id)
        title = media.get('name', 'Unknown Series')
        
    # Standard open-source Big Buck Bunny HLS stream for testing
    video_url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    
    return render(request, 'playback/watch.html', {
        'media': media,
        'title': title,
        'video_url': video_url,
        'media_type': media_type,
        'tmdb_id': tmdb_id
    })
