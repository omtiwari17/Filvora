import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.tmdb.client import TMDBClient
from apps.watch.models import WatchProgress
from apps.playback.models import PlaybackServerPreference
from apps.playback.providers import registry, get_provider

def format_time(seconds: float) -> str:
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    remaining_seconds = secs % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes:02d}:{remaining_seconds:02d}"

@login_required
def watch(request, media_type, tmdb_id, season=None, episode=None):
    client = TMDBClient()
    server_id = request.GET.get('server')
    s_num = season if season is not None else (1 if media_type == 'tv' else None)
    ep_num = episode if episode is not None else (1 if media_type == 'tv' else None)

    # If no server specified, check user's saved preferred server for this title & active profile
    if not server_id and request.user.is_authenticated:
        from apps.accounts.utils import get_active_profile
        profile = get_active_profile(request)
        pref = PlaybackServerPreference.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type,
            season=s_num,
            episode=ep_num
        ).first()
        if pref:
            server_id = pref.provider_id

    provider = get_provider(server_id)
    ordered_providers = registry.get_ordered_providers(preferred_id=provider.id)
    next_provider = registry.get_next_provider(provider.id)

    previous_episode = None
    if media_type == 'movie':
        media = client.get_movie(tmdb_id)
        title = media.get('title', 'Unknown Movie')
        source = provider.get_movie_source(tmdb_id)
        video_url = source.url
        next_episode = None
    else:
        media = client.get_tv(tmdb_id)
        series_name = media.get('name', 'Unknown Series')
        title = f"{series_name} — S{s_num}:E{ep_num}"
        source = provider.get_episode_source(tmdb_id, s_num, ep_num)
        video_url = source.url
        
        # Calculate accurate next & previous episode with season rollover
        if ep_num > 1:
            previous_episode = {
                'season': s_num,
                'episode': ep_num - 1,
                'url': f"/watch/tv/{tmdb_id}/{s_num}/{ep_num - 1}/"
            }

        # Check season episodes to determine if next episode is in current season or next season
        current_season_data = client.get_tv_season(tmdb_id, s_num)
        episodes_in_season = current_season_data.get('episodes', [])
        total_eps_in_season = len(episodes_in_season) if episodes_in_season else 99

        next_ep_title = ""
        next_ep_still = ""
        next_s_num = s_num
        next_e_num = ep_num + 1

        if ep_num < total_eps_in_season:
            next_s_num = s_num
            next_e_num = ep_num + 1
            # Find next episode metadata
            for ep in episodes_in_season:
                if ep.get('episode_number') == next_e_num:
                    next_ep_title = ep.get('name', f"Episode {next_e_num}")
                    next_ep_still = ep.get('still_path', '')
                    break
        else:
            # Check if next season exists
            seasons_list = [s for s in media.get('seasons', []) if s.get('season_number', 0) > s_num]
            if seasons_list:
                next_s_num = s_num + 1
                next_e_num = 1
                next_season_data = client.get_tv_season(tmdb_id, next_s_num)
                next_season_eps = next_season_data.get('episodes', [])
                if next_season_eps:
                    next_ep_title = next_season_eps[0].get('name', "Episode 1")
                    next_ep_still = next_season_eps[0].get('still_path', '')
            else:
                next_s_num = None
                next_e_num = None

        if next_s_num and next_e_num:
            next_episode = {
                'season': next_s_num,
                'episode': next_e_num,
                'title': next_ep_title or f"Episode {next_e_num}",
                'still_path': next_ep_still,
                'series_name': series_name,
                'url': f"/watch/tv/{tmdb_id}/{next_s_num}/{next_e_num}/"
            }
        else:
            next_episode = None
    
    # Check if user has saved watch progress to resume for active profile
    resume_position = 0
    resume_formatted = ""
    from apps.accounts.utils import get_active_profile
    profile = get_active_profile(request)
    progress = WatchProgress.objects.filter(
        user=request.user,
        profile=profile,
        tmdb_id=tmdb_id,
        media_type=media_type,
        season=s_num if media_type == 'tv' else None,
        episode=ep_num if media_type == 'tv' else None
    ).first()
    
    if progress and not progress.completed and progress.position_seconds >= 30:
        resume_position = round(progress.position_seconds, 1)
        resume_formatted = format_time(progress.position_seconds)

    return render(request, 'playback/watch.html', {
        'media': media,
        'title': title,
        'source': source,
        'video_url': video_url,
        'media_type': media_type,
        'tmdb_id': tmdb_id,
        'season': s_num or '',
        'episode': ep_num or '',
        'resume_position': resume_position,
        'resume_formatted': resume_formatted,
        'providers': ordered_providers,
        'current_server': provider.id,
        'current_provider': provider,
        'next_provider': next_provider,
        'previous_episode': previous_episode,
        'next_episode': next_episode,
    })


@csrf_exempt
@login_required
def report_server_success(request):
    """Saves the working server provider for this user profile & title for future instant load."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        provider_id = data.get('provider_id')
        season = int(data.get('season')) if data.get('season') else None
        episode = int(data.get('episode')) if data.get('episode') else None

        if provider_id:
            from apps.accounts.utils import get_active_profile
            profile = get_active_profile(request)
            PlaybackServerPreference.objects.update_or_create(
                user=request.user,
                profile=profile,
                tmdb_id=tmdb_id,
                media_type=media_type,
                season=season,
                episode=episode,
                defaults={'provider_id': provider_id}
            )

        return JsonResponse({'status': 'ok', 'saved_provider': provider_id})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def diagnostics(request):
    """Returns diagnostics for all registered playback providers."""
    results = registry.run_diagnostics()
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({'providers': results})
    return render(request, 'playback/diagnostics.html', {'diagnostics': results})
