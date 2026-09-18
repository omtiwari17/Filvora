from apps.accounts.utils import get_active_profile
from apps.watch.models import WatchProgress, UserRating
from apps.library.models import LibraryItem

def user_watch_context(request):
    """
    Provides active profile's watched IDs, rating dictionaries, and saved library IDs
    globally to all templates for instant, unified in-card state rendering.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'user_watched_movie_ids': set(),
            'user_watched_tv_ids': set(),
            'user_watched_ids': set(),
            'user_movie_ratings': {},
            'user_tv_ratings': {},
            'user_ratings': {},
            'user_saved_ids': set(),
        }

    profile = get_active_profile(request)

    # 1. Watched content (completed=True)
    watched_qs = WatchProgress.objects.filter(user=user, profile=profile, completed=True).values_list('tmdb_id', 'media_type')
    watched_movie_ids = set()
    watched_tv_ids = set()
    for tmdb_id, media_type in watched_qs:
        if media_type == 'tv':
            watched_tv_ids.add(tmdb_id)
        else:
            watched_movie_ids.add(tmdb_id)

    # 2. User ratings
    rating_qs = UserRating.objects.filter(user=user, profile=profile).values_list('tmdb_id', 'media_type', 'score')
    movie_ratings = {}
    tv_ratings = {}
    all_ratings = {}
    for tmdb_id, media_type, score in rating_qs:
        all_ratings[tmdb_id] = score
        all_ratings[str(tmdb_id)] = score
        if media_type == 'tv':
            tv_ratings[tmdb_id] = score
            tv_ratings[str(tmdb_id)] = score
        else:
            movie_ratings[tmdb_id] = score
            movie_ratings[str(tmdb_id)] = score

    # 3. Library saved IDs (fallback / universal availability)
    saved_ids = set(
        LibraryItem.objects.filter(user=user, profile=profile).values_list('tmdb_id', flat=True)
    )

    return {
        'user_watched_movie_ids': watched_movie_ids,
        'user_watched_tv_ids': watched_tv_ids,
        'user_watched_ids': watched_movie_ids | watched_tv_ids,
        'user_movie_ratings': movie_ratings,
        'user_tv_ratings': tv_ratings,
        'user_ratings': all_ratings,
        'user_saved_ids': saved_ids,
    }
