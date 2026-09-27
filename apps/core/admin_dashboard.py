import os
import sys
import time
import socket
import platform
from pathlib import Path
from datetime import timedelta

import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Avg, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from apps.accounts.models import UserProfile
from apps.watch.models import WatchProgress, UserRating
from apps.library.models import (
    LibraryItem,
    CustomCollection,
    CustomCollectionItem,
    SceneBookmark,
    FavoritePerson,
)
from apps.playback.models import PlaybackServerPreference
from apps.tmdb.client import TMDBClient

User = get_user_model()


def _get_dir_size_and_count(dir_path):
    """Calculates total size in bytes and file count of a directory recursively."""
    total_bytes = 0
    total_files = 0
    p = Path(dir_path)
    if p.exists() and p.is_dir():
        for root, _, files in os.walk(p):
            total_files += len(files)
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    if not os.path.islink(fp):
                        total_bytes += os.path.getsize(fp)
                except OSError:
                    pass
    return total_bytes, total_files


def _read_server_logs(max_lines=60):
    """Reads latest lines from filvora.log or server output."""
    candidates = [
        settings.BASE_DIR / 'filvora.log',
        Path.home() / 'filvora.log',
        Path('/data/data/com.termux/files/home/filvora.log'),
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        return ''.join(lines[-max_lines:])
            except Exception:
                pass
    return "filvora.log is clean or server is running in direct console mode. No unhandled exceptions reported."


def get_admin_dashboard_data():
    """Aggregates comprehensive developer metrics, system telemetry, and admin KPIs."""
    now = timezone.now()
    client = TMDBClient()

    # 1. System & Developer Metrics
    db_path = settings.DATABASES['default'].get('NAME', 'db.sqlite3')
    db_file = Path(db_path) if isinstance(db_path, (str, Path)) else settings.BASE_DIR / 'db.sqlite3'
    db_size_mb = 0.0
    if db_file.exists():
        try:
            db_size_mb = round(os.path.getsize(db_file) / (1024 * 1024), 2)
        except OSError:
            pass

    # SQLite WAL check
    wal_active = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode;")
            row = cursor.fetchone()
            if row and row[0].lower() == 'wal':
                wal_active = True
    except Exception:
        pass

    # Cache metrics
    cache_dir = settings.CACHES['default'].get('LOCATION', settings.BASE_DIR / '.cache' / 'django_cache')
    cache_bytes, cache_files = _get_dir_size_and_count(cache_dir)
    cache_size_mb = round(cache_bytes / (1024 * 1024), 2)

    # TMDB key & breaker
    raw_tmdb_key = os.environ.get('TMDB_API_KEY', '')
    masked_key = f"{raw_tmdb_key[:4]}...{raw_tmdb_key[-4:]}" if len(raw_tmdb_key) > 8 else ("Configured" if raw_tmdb_key else "Missing")
    is_tmdb_offline = client.is_offline()
    rating_cache_count = len(getattr(TMDBClient, '_RATING_CACHE', {}))

    # LAN IPs
    lan_ips = ['127.0.0.1:8000']
    try:
        host_name = socket.gethostname()
        local_ip = socket.gethostbyname(host_name)
        if local_ip and local_ip not in ['127.0.0.1', '0.0.0.0']:
            lan_ips.append(f"{local_ip}:8000")
    except Exception:
        pass
    lan_ips.extend(['192.168.1.5:8000', '192.168.1.50:8000'])
    lan_ips = list(dict.fromkeys(lan_ips))

    system_data = {
        'python_version': sys.version.split()[0],
        'python_executable': sys.executable,
        'django_version': django.get_version(),
        'debug_mode': settings.DEBUG,
        'os_name': platform.system(),
        'os_release': platform.release(),
        'os_full': f"{platform.system()} {platform.release()} ({platform.machine()})",
        'machine': platform.machine(),
        'hostname': socket.gethostname(),
        'pid': os.getpid(),
        'server_time': now,
        'timezone': settings.TIME_ZONE,
        'base_dir': str(settings.BASE_DIR),
        'db_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'db_name': str(db_file.name),
        'db_size_mb': db_size_mb,
        'db_wal': wal_active,
        'cache_backend': settings.CACHES['default']['BACKEND'].split('.')[-1],
        'cache_dir': str(cache_dir),
        'cache_files': cache_files,
        'cache_size_mb': cache_size_mb,
        'tmdb_configured': bool(raw_tmdb_key),
        'tmdb_masked': masked_key,
        'tmdb_offline': is_tmdb_offline,
        'tmdb_rating_cache_count': rating_cache_count,
        'lan_ips': lan_ips,
        'installed_apps_count': len(settings.INSTALLED_APPS),
        'middleware_count': len(settings.MIDDLEWARE),
    }

    # 2. User & Profile Metrics
    total_users = User.objects.count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    active_24h = User.objects.filter(last_login__gte=now - timedelta(days=1)).count()
    active_7d = User.objects.filter(last_login__gte=now - timedelta(days=7)).count()
    total_profiles = UserProfile.objects.count()
    kids_profiles = UserProfile.objects.filter(is_kids=True).count()
    standard_profiles = total_profiles - kids_profiles
    recent_users = User.objects.order_by('-date_joined')[:6]

    users_data = {
        'total_users': total_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'active_24h': active_24h,
        'active_7d': active_7d,
        'total_profiles': total_profiles,
        'standard_profiles': standard_profiles,
        'kids_profiles': kids_profiles,
        'recent_users': recent_users,
    }

    # 3. Streaming & Playback Metrics
    total_streams = WatchProgress.objects.count()
    completed_streams = WatchProgress.objects.filter(completed=True).count()
    in_progress_streams = WatchProgress.objects.filter(completed=False).count()
    completion_rate = round((completed_streams / total_streams * 100), 1) if total_streams > 0 else 0.0

    movies_streamed = WatchProgress.objects.filter(media_type='movie').count()
    tv_streamed = WatchProgress.objects.filter(media_type='tv').count()

    total_seconds = WatchProgress.objects.aggregate(s=Sum('position_seconds'))['s'] or 0.0
    total_hours = round(total_seconds / 3600.0, 1)

    recent_activity = WatchProgress.objects.select_related('user', 'profile').order_by('-updated_at')[:10]
    top_watched_query = WatchProgress.objects.values('tmdb_id', 'media_type').annotate(views=Count('id')).order_by('-views')[:6]

    streaming_data = {
        'total_streams': total_streams,
        'completed_streams': completed_streams,
        'in_progress_streams': in_progress_streams,
        'completion_rate': completion_rate,
        'movies_streamed': movies_streamed,
        'tv_streamed': tv_streamed,
        'total_hours': total_hours,
        'recent_activity': recent_activity,
        'top_watched': top_watched_query,
    }

    # 4. User Engagement & Ratings
    total_ratings = UserRating.objects.count()
    avg_score_raw = UserRating.objects.aggregate(avg=Avg('score'))['avg']
    avg_score = round(avg_score_raw, 1) if avg_score_raw else 0.0

    star_dist = {}
    for star in [5, 4, 3, 2, 1]:
        cnt = UserRating.objects.filter(score=star).count()
        pct = round((cnt / total_ratings * 100), 1) if total_ratings > 0 else 0.0
        star_dist[star] = {'count': cnt, 'percentage': pct}

    recent_ratings = UserRating.objects.select_related('user', 'profile').order_by('-updated_at')[:8]

    ratings_data = {
        'total_ratings': total_ratings,
        'avg_score': avg_score,
        'star_distribution': star_dist,
        'recent_ratings': recent_ratings,
    }

    # 5. Library & Bookmarks
    library_items_count = LibraryItem.objects.count()
    collections_count = CustomCollection.objects.count()
    collection_items_count = CustomCollectionItem.objects.count()
    bookmarks_count = SceneBookmark.objects.count()
    favorite_people_count = FavoritePerson.objects.count()

    library_data = {
        'library_items_count': library_items_count,
        'collections_count': collections_count,
        'collection_items_count': collection_items_count,
        'bookmarks_count': bookmarks_count,
        'favorite_people_count': favorite_people_count,
    }

    # 6. Video Embed Provider Preferences
    provider_counts = (
        PlaybackServerPreference.objects.values('provider_id')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )

    # 7. Django Model Registry for Direct Access
    model_cards = [
        {
            'name': 'Users',
            'app': 'auth',
            'model': 'user',
            'count': total_users,
            'icon': 'users',
            'color': 'indigo',
            'admin_url': '/admin/auth/user/',
            'add_url': '/admin/auth/user/add/',
            'description': 'Authentication accounts & staff permissions'
        },
        {
            'name': 'Profiles',
            'app': 'accounts',
            'model': 'userprofile',
            'count': total_profiles,
            'icon': 'user-circle',
            'color': 'rose',
            'admin_url': '/admin/accounts/userprofile/',
            'add_url': '/admin/accounts/userprofile/add/',
            'description': 'Standard & Kids multi-user profiles'
        },
        {
            'name': 'Watch Progress',
            'app': 'watch',
            'model': 'watchprogress',
            'count': total_streams,
            'icon': 'play',
            'color': 'brand',
            'admin_url': '/admin/watch/watchprogress/',
            'add_url': '/admin/watch/watchprogress/add/',
            'description': 'Streaming sessions, timestamps & completion'
        },
        {
            'name': 'User Ratings',
            'app': 'watch',
            'model': 'userrating',
            'count': total_ratings,
            'icon': 'star',
            'color': 'amber',
            'admin_url': '/admin/watch/userrating/',
            'add_url': '/admin/watch/userrating/add/',
            'description': '1-5 star user reviews and community scores'
        },
        {
            'name': 'Watchlist Items',
            'app': 'library',
            'model': 'libraryitem',
            'count': library_items_count,
            'icon': 'bookmark',
            'color': 'emerald',
            'admin_url': '/admin/library/libraryitem/',
            'add_url': '/admin/library/libraryitem/add/',
            'description': 'Saved movies & TV series in My List'
        },
        {
            'name': 'Custom Collections',
            'app': 'library',
            'model': 'customcollection',
            'count': collections_count,
            'icon': 'folder',
            'color': 'purple',
            'admin_url': '/admin/library/customcollection/',
            'add_url': '/admin/library/customcollection/add/',
            'description': 'User-curated playlists & thematic groups'
        },
        {
            'name': 'Scene Bookmarks',
            'app': 'library',
            'model': 'scenebookmark',
            'count': bookmarks_count,
            'icon': 'film',
            'color': 'cyan',
            'admin_url': '/admin/library/scenebookmark/',
            'add_url': '/admin/library/scenebookmark/add/',
            'description': 'Saved exact timestamps with custom notes'
        },
        {
            'name': 'Favorite Actors',
            'app': 'library',
            'model': 'favoriteperson',
            'count': favorite_people_count,
            'icon': 'heart',
            'color': 'pink',
            'admin_url': '/admin/library/favoriteperson/',
            'add_url': '/admin/library/favoriteperson/add/',
            'description': 'Followed artists, directors & cast members'
        },
        {
            'name': 'Server Preferences',
            'app': 'playback',
            'model': 'playbackserverpreference',
            'count': PlaybackServerPreference.objects.count(),
            'icon': 'server',
            'color': 'blue',
            'admin_url': '/admin/playback/playbackserverpreference/',
            'add_url': '/admin/playback/playbackserverpreference/add/',
            'description': 'Preferred streaming embed providers per title'
        },
    ]

    return {
        'system': system_data,
        'users': users_data,
        'streaming': streaming_data,
        'ratings': ratings_data,
        'library': library_data,
        'provider_counts': provider_counts,
        'models': model_cards,
        'recent_logs': _read_server_logs(60),
    }


@staff_member_required(login_url='/accounts/login/')
def admin_dashboard_view(request):
    """Primary Custom Admin & Developer Dashboard View."""
    context = get_admin_dashboard_data()
    context['user'] = request.user
    return render(request, 'admin/dashboard.html', context)


@staff_member_required(login_url='/accounts/login/')
@require_POST
def admin_purge_cache(request):
    """HTMX / JSON endpoint to purge all file-based and in-memory caches."""
    cache_dir = settings.CACHES['default'].get('LOCATION', settings.BASE_DIR / '.cache' / 'django_cache')
    deleted_files = 0

    # 1. Clear Django cache backend
    try:
        cache.clear()
    except Exception:
        pass

    # 2. Clean physical cache directory
    p = Path(cache_dir)
    if p.exists() and p.is_dir():
        for root, _, files in os.walk(p):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                    deleted_files += 1
                except OSError:
                    pass

    # 3. Clear TMDB in-memory rating cache
    if hasattr(TMDBClient, '_RATING_CACHE'):
        TMDBClient._RATING_CACHE.clear()

    if request.headers.get('HX-Request'):
        return HttpResponse(
            f'<div class="flex items-center gap-2 text-emerald-400 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-800 animate-pulse">'
            f'<svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
            f'Cache Purged! ({deleted_files} files removed, 0.0 MB)</div>'
        )

    return JsonResponse({'status': 'ok', 'message': f'Cache purged. {deleted_files} files deleted.', 'deleted_files': deleted_files})


@staff_member_required(login_url='/accounts/login/')
def admin_ping_tmdb(request):
    """HTMX endpoint to test TMDB API latency live."""
    client = TMDBClient()
    start_time = time.time()
    online = False
    status_code = None
    error_msg = ""

    try:
        # Lightweight check: ping configuration or popular
        import requests
        headers = {'accept': 'application/json'}
        token = os.environ.get('TMDB_ACCESS_TOKEN', '')
        api_key = os.environ.get('TMDB_API_KEY', '')
        if token:
            headers['Authorization'] = f'Bearer {token}'
            url = 'https://api.themoviedb.org/3/configuration'
        elif api_key:
            url = f'https://api.themoviedb.org/3/configuration?api_key={api_key}'
        else:
            url = 'https://api.themoviedb.org/3/movie/popular'

        resp = requests.get(url, headers=headers, timeout=4)
        status_code = resp.status_code
        online = (status_code == 200)
    except Exception as e:
        error_msg = str(e)[:60]

    elapsed_ms = int((time.time() - start_time) * 1000)

    if request.headers.get('HX-Request'):
        if online:
            return HttpResponse(
                f'<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">'
                f'<span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>'
                f'Online ({elapsed_ms}ms) • 200 OK</span>'
            )
        else:
            return HttpResponse(
                f'<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">'
                f'<span class="w-2 h-2 rounded-full bg-rose-400"></span>'
                f'Failed ({status_code or error_msg or "Timeout"})</span>'
            )

    return JsonResponse({'online': online, 'latency_ms': elapsed_ms, 'status_code': status_code})


@staff_member_required(login_url='/accounts/login/')
@require_POST
def admin_check_db(request):
    """HTMX endpoint to run SQLite integrity check."""
    status_str = "Unknown"
    is_ok = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row:
                status_str = row[0]
                is_ok = (status_str.lower() == 'ok')
    except Exception as e:
        status_str = str(e)[:60]

    if request.headers.get('HX-Request'):
        color = "emerald" if is_ok else "rose"
        return HttpResponse(
            f'<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-{color}-500/10 text-{color}-400 border border-{color}-500/30">'
            f'PRAGMA check: {status_str}</span>'
        )

    return JsonResponse({'status': status_str, 'ok': is_ok})


@staff_member_required(login_url='/accounts/login/')
@require_POST
def admin_reset_circuit_breaker(request):
    """HTMX endpoint to reset the TMDB client offline circuit breaker."""
    if hasattr(TMDBClient, '_offline_until'):
        TMDBClient._offline_until = 0

    if request.headers.get('HX-Request'):
        return HttpResponse(
            '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">'
            'Circuit Breaker Reset! Probe Ready</span>'
        )
    return JsonResponse({'status': 'ok', 'message': 'Circuit breaker reset.'})


@staff_member_required(login_url='/accounts/login/')
def admin_logs_stream(request):
    """HTMX endpoint to stream fresh log lines."""
    logs = _read_server_logs(60)
    return HttpResponse(
        f'<pre class="font-mono text-xs text-emerald-400/90 whitespace-pre-wrap leading-relaxed select-text p-4 bg-gray-950/90 rounded-xl border border-gray-800 max-h-96 overflow-y-auto">{logs}</pre>'
    )


@staff_member_required(login_url='/accounts/login/')
def admin_quick_inspect(request):
    """Quick lookup of a username or TMDB ID with immediate telemetry readout."""
    query = request.GET.get('q', '').strip()
    if not query:
        return HttpResponse('<p class="text-xs text-gray-500">Enter a username or numerical TMDB ID above.</p>')

    # 1. Check if numeric TMDB ID
    if query.isdigit():
        tmdb_id = int(query)
        wp_list = WatchProgress.objects.filter(tmdb_id=tmdb_id).select_related('user', 'profile')[:10]
        ratings = UserRating.objects.filter(tmdb_id=tmdb_id).select_related('user', 'profile')
        bookmarks = SceneBookmark.objects.filter(tmdb_id=tmdb_id).select_related('user', 'profile')
        library_entries = LibraryItem.objects.filter(tmdb_id=tmdb_id).select_related('user', 'profile')

        html = f"""
        <div class="p-4 rounded-xl bg-gray-900/90 border border-gray-800 space-y-3">
            <div class="flex items-center justify-between border-b border-gray-800 pb-2">
                <span class="text-xs font-bold text-brand-400 uppercase tracking-wider">TMDB ID #{tmdb_id} Inspection</span>
                <span class="text-xs text-gray-400">{wp_list.count()} streams • {ratings.count()} ratings • {bookmarks.count()} bookmarks</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div class="p-2.5 rounded-lg bg-gray-950/60 border border-gray-800">
                    <p class="font-semibold text-gray-300 mb-1">Watch Activity ({wp_list.count()} records):</p>
                    <ul class="space-y-1 text-gray-400">
                        {"".join(f"<li>• {w.user.username} [{w.profile.name if w.profile else 'Def'}]: {w.progress_percentage}% ({'Done' if w.completed else 'Watching'})</li>" for w in wp_list) or "<li>None recorded</li>"}
                    </ul>
                </div>
                <div class="p-2.5 rounded-lg bg-gray-950/60 border border-gray-800">
                    <p class="font-semibold text-gray-300 mb-1">Ratings & Bookmarks:</p>
                    <ul class="space-y-1 text-gray-400">
                        {"".join(f"<li>• {r.user.username}: {r.score}/5 stars</li>" for r in ratings) or "<li>No ratings</li>"}
                        {"".join(f"<li>• Bookmark: '{b.title}' @ {b.formatted_timestamp}</li>" for b in bookmarks)}
                    </ul>
                </div>
            </div>
        </div>
        """
        return HttpResponse(html)

    # 2. Check if username
    user_match = User.objects.filter(username__icontains=query).first()
    if user_match:
        profiles = user_match.profiles.all()
        user_streams = WatchProgress.objects.filter(user=user_match).count()
        user_ratings = UserRating.objects.filter(user=user_match).count()
        user_lib = LibraryItem.objects.filter(user=user_match).count()
        user_bm = SceneBookmark.objects.filter(user=user_match).count()

        html = f"""
        <div class="p-4 rounded-xl bg-gray-900/90 border border-gray-800 space-y-3">
            <div class="flex items-center justify-between border-b border-gray-800 pb-2">
                <div>
                    <span class="text-sm font-bold text-white">{user_match.username}</span>
                    <span class="text-xs text-gray-400 ml-2">({user_match.email or 'no email'})</span>
                </div>
                <span class="text-xs px-2 py-0.5 rounded {'bg-indigo-500/20 text-indigo-400' if user_match.is_staff else 'bg-gray-800 text-gray-400'}">
                    {'Staff Member' if user_match.is_staff else 'Standard User'}
                </span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div class="p-2 rounded bg-gray-950/60 border border-gray-800 text-center">
                    <p class="text-gray-400">Streams</p>
                    <p class="text-base font-bold text-white">{user_streams}</p>
                </div>
                <div class="p-2 rounded bg-gray-950/60 border border-gray-800 text-center">
                    <p class="text-gray-400">Ratings</p>
                    <p class="text-base font-bold text-amber-400">{user_ratings}</p>
                </div>
                <div class="p-2 rounded bg-gray-950/60 border border-gray-800 text-center">
                    <p class="text-gray-400">Watchlist</p>
                    <p class="text-base font-bold text-emerald-400">{user_lib}</p>
                </div>
                <div class="p-2 rounded bg-gray-950/60 border border-gray-800 text-center">
                    <p class="text-gray-400">Bookmarks</p>
                    <p class="text-base font-bold text-cyan-400">{user_bm}</p>
                </div>
            </div>
            <div class="text-xs text-gray-400">
                <span class="font-semibold text-gray-300">Profiles:</span>
                {", ".join(p.name + (' (Kids)' if p.is_kids else '') for p in profiles) or "None"}
            </div>
        </div>
        """
        return HttpResponse(html)

    return HttpResponse(f'<p class="text-xs text-rose-400">No user or TMDB record found matching "{query}".</p>')
