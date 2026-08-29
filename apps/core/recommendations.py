from collections import Counter
from apps.tmdb.client import TMDBClient
from apps.watch.models import WatchProgress, UserRating
from apps.library.models import LibraryItem

class RecommendationEngine:
    def __init__(self):
        self.client = TMDBClient()

    def get_user_affinity_genres(self, user):
        """Calculates genre frequency weights from user's watch progress and library."""
        if not user or not user.is_authenticated:
            return []

        genre_counts = Counter()
        
        # 1. Signals from Watch Progress
        progress_items = WatchProgress.objects.filter(user=user).order_by('-updated_at')[:20]
        for p in progress_items:
            weight = 3 if p.completed else 1
            if p.media_type == 'movie':
                details = self.client.get_movie_details(p.tmdb_id)
            else:
                details = self.client.get_tv_details(p.tmdb_id)

            for g in details.get('genres', []):
                gid = g.get('id') if isinstance(g, dict) else g
                if gid:
                    genre_counts[gid] += weight

        # 2. Signals from Library
        library_items = LibraryItem.objects.filter(user=user)[:20]
        for item in library_items:
            if item.media_type == 'movie':
                details = self.client.get_movie_details(item.tmdb_id)
            else:
                details = self.client.get_tv_details(item.tmdb_id)

            for g in details.get('genres', []):
                gid = g.get('id') if isinstance(g, dict) else g
                if gid:
                    genre_counts[gid] += 2

        # 3. Signals from User Ratings (strongest personalization signal)
        rated_items = UserRating.objects.filter(user=user).order_by('-updated_at')[:20]
        for r in rated_items:
            if r.media_type == 'movie':
                details = self.client.get_movie_details(r.tmdb_id)
            else:
                details = self.client.get_tv_details(r.tmdb_id)

            # High ratings (4-5) = strong positive signal, low (1-2) = negative signal
            if r.score >= 4:
                weight = 5
            elif r.score == 3:
                weight = 2
            else:
                weight = -2

            for g in details.get('genres', []):
                gid = g.get('id') if isinstance(g, dict) else g
                if gid:
                    genre_counts[gid] += weight

        # Return top genres sorted by frequency
        return [gid for gid, _ in genre_counts.most_common(3)]

    def get_personalized_recommendations(self, user, limit=12):
        """Returns deterministic curated recommendations tailored to user affinity."""
        if not user or not user.is_authenticated:
            return self.client.get_top_rated_movies()[:limit]

        top_genres = self.get_user_affinity_genres(user)
        if top_genres:
            primary_genre = top_genres[0]
            results = self.client.discover_content(
                media_type='movie',
                genre_id=primary_genre,
                min_rating=7.0,
                sort_by='vote_average.desc'
            )
            if results:
                return results[:limit]

        return self.client.get_top_rated_movies()[:limit]

    def get_because_you_watched(self, user):
        """Returns recommendations based on the user's latest watched title."""
        if not user or not user.is_authenticated:
            return None

        latest_progress = WatchProgress.objects.filter(user=user, position_seconds__gt=30).order_by('-updated_at').first()
        if not latest_progress:
            # Fallback to latest library item
            latest_lib = LibraryItem.objects.filter(user=user).order_by('-added_at').first()
            if not latest_lib:
                return None
            mtype = latest_lib.media_type
            tid = latest_lib.tmdb_id
        else:
            mtype = latest_progress.media_type
            tid = latest_progress.tmdb_id

        if mtype == 'movie':
            details = self.client.get_movie_details(tid)
            title = details.get('title', f"Movie {tid}")
        else:
            details = self.client.get_tv_details(tid)
            title = details.get('name', f"Series {tid}")

        recs = details.get('recommendations', {}).get('results', [])
        if not recs:
            # Fallback to discover by first genre
            genres = details.get('genres', [])
            if genres:
                gid = genres[0].get('id') if isinstance(genres[0], dict) else genres[0]
                recs = self.client.discover_content(media_type=mtype, genre_id=gid, min_rating=7.0)

        return {
            'title': title,
            'media_type': mtype,
            'items': recs[:10]
        }
