import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from apps.downloads.models import DownloadJob
from apps.downloads.services.manager import DownloadManager
from apps.downloads.services.storage import format_file_size
from apps.downloads.providers.registry import get_available_qualities, find_provider


@login_required
def start_download(request):
    """Create a new download job and redirect to dashboard."""
    if request.method == 'POST':
        tmdb_id = int(request.POST.get('tmdb_id'))
        media_type = request.POST.get('media_type', 'movie')
        season = int(request.POST.get('season')) if request.POST.get('season') else None
        episode = int(request.POST.get('episode')) if request.POST.get('episode') else None
        quality = request.POST.get('quality', '1080p')

        job = DownloadManager.create_job(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type=media_type,
            season=season,
            episode=episode,
            quality=quality
        )
        return redirect('/downloads/')
    return HttpResponse("POST required", status=400)


@login_required
def downloads_dashboard(request):
    """Main downloads dashboard with HTMX live-polling job list."""
    jobs = DownloadJob.objects.filter(user=request.user).order_by('-created_at')[:20]

    # Enrich jobs with formatted file sizes
    for job in jobs:
        job.file_size_display = format_file_size(job.file_size) if job.file_size else ''

    return render(request, 'downloads/dashboard.html', {
        'jobs': jobs,
        'active_count': sum(1 for j in jobs if j.status in ['QUEUED', 'DOWNLOADING', 'PROCESSING']),
        'ready_count': sum(1 for j in jobs if j.status == 'READY'),
        'failed_count': sum(1 for j in jobs if j.status == 'FAILED'),
    })


@login_required
def download_status_partial(request):
    """HTMX partial for live-polling job status updates."""
    jobs = DownloadJob.objects.filter(user=request.user).order_by('-created_at')[:20]

    for job in jobs:
        job.file_size_display = format_file_size(job.file_size) if job.file_size else ''

    return render(request, 'downloads/partials/jobs_list.html', {'jobs': jobs})


@login_required
def download_file(request, job_id):
    """Serve the completed download file via browser download."""
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if job.status != 'READY' or not job.temporary_path or not os.path.exists(job.temporary_path):
        raise Http404("Download file is not ready or has expired.")

    response = FileResponse(open(job.temporary_path, 'rb'), as_attachment=True, filename=job.filename)
    return response


@login_required
def cancel_download(request, job_id):
    """Cancel an active or queued download job."""
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if request.method == 'POST':
        # Clean up temp files
        from apps.downloads.services.cleanup import cleanup_job
        cleanup_job(str(job.id))

        if job.temporary_path and os.path.exists(job.temporary_path):
            try:
                os.remove(job.temporary_path)
            except OSError:
                pass

        job.status = 'CANCELLED'
        job.temporary_path = ''
        job.save()
    return redirect('/downloads/')


@login_required
def retry_download(request, job_id):
    """Retry a failed or cancelled download job."""
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if request.method == 'POST':
        if job.status in ('FAILED', 'CANCELLED'):
            DownloadManager.retry_job(job.id)
    return redirect('/downloads/')


@login_required
def download_dialog(request):
    """
    Return the download quality selection dialog as an HTMX partial.

    Query params: tmdb_id, media_type, season (optional), episode (optional)
    """
    tmdb_id = int(request.GET.get('tmdb_id', 0))
    media_type = request.GET.get('media_type', 'movie')
    season = request.GET.get('season', '')
    episode = request.GET.get('episode', '')

    # Get title from TMDB
    from apps.tmdb.client import TMDBClient
    client = TMDBClient()

    if media_type == 'movie':
        details = client.get_movie(tmdb_id)
        title = details.get('title', f'Movie {tmdb_id}')
        year = (details.get('release_date') or '')[:4]
    else:
        details = client.get_tv(tmdb_id)
        title = details.get('name', f'Series {tmdb_id}')
        year = (details.get('first_air_date') or '')[:4]

    # Get available qualities
    season_int = int(season) if season else None
    episode_int = int(episode) if episode else None
    qualities = get_available_qualities(tmdb_id, media_type, season_int, episode_int)

    # Build display title
    if media_type == 'tv' and season and episode:
        display_title = f"{title} S{int(season):02d}E{int(episode):02d}"
    else:
        display_title = f"{title} ({year})" if year else title

    return render(request, 'downloads/partials/download_dialog.html', {
        'tmdb_id': tmdb_id,
        'media_type': media_type,
        'season': season,
        'episode': episode,
        'title': display_title,
        'qualities': qualities,
        'default_quality': qualities[0] if qualities else '1080p',
    })


@login_required
def delete_job(request, job_id):
    """Delete a completed/failed/cancelled job from the dashboard."""
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if request.method == 'POST':
        if job.status in ('READY', 'FAILED', 'CANCELLED'):
            from apps.downloads.services.cleanup import cleanup_job
            cleanup_job(str(job.id))
            job.delete()
    return redirect('/downloads/')
