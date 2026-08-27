import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from apps.downloads.models import DownloadJob
from apps.downloads.services.manager import DownloadManager

@login_required
def start_download(request):
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
    jobs = DownloadJob.objects.filter(user=request.user).order_by('-created_at')[:20]
    return render(request, 'downloads/dashboard.html', {
        'jobs': jobs,
        'active_count': sum(1 for j in jobs if j.status in ['QUEUED', 'DOWNLOADING', 'PROCESSING']),
        'ready_count': sum(1 for j in jobs if j.status == 'READY')
    })

@login_required
def download_status_partial(request):
    jobs = DownloadJob.objects.filter(user=request.user).order_by('-created_at')[:20]
    return render(request, 'downloads/partials/jobs_list.html', {'jobs': jobs})

@login_required
def download_file(request, job_id):
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if job.status != 'READY' or not job.temporary_path or not os.path.exists(job.temporary_path):
        raise Http404("Download file is not ready or has expired.")

    response = FileResponse(open(job.temporary_path, 'rb'), as_attachment=True, filename=job.filename)
    return response

@login_required
def cancel_download(request, job_id):
    job = get_object_or_404(DownloadJob, id=job_id, user=request.user)
    if request.method == 'POST':
        if job.temporary_path and os.path.exists(job.temporary_path):
            try:
                os.remove(job.temporary_path)
            except OSError:
                pass
        job.status = 'CANCELLED'
        job.save()
    return redirect('/downloads/')
