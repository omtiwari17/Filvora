import re
from collections import Counter
from django.db.models import Q
from apps.tmdb.client import TMDBClient
from apps.watch.models import WatchProgress, UserRating
from apps.library.models import LibraryItem

class RecommendationEngine:
    def __init__(self):
        self.client = TMDBClient()

    def get_user_affinity_genres(self, user, profile=None):
        """Calculates genre frequency weights from user's watch progress, library, and ratings for active profile."""
        if not user or not user.is_authenticated:
            return []

        genre_counts = Counter()
        
        # 1. Signals from Watch Progress
        progress_qs = WatchProgress.objects.filter(user=user)
        if profile:
            progress_qs = progress_qs.filter(profile=profile)
        progress_items = progress_qs.order_by('-updated_at')[:20]
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
        library_qs = LibraryItem.objects.filter(user=user)
        if profile:
            library_qs = library_qs.filter(profile=profile)
        library_items = library_qs.order_by('-added_at')[:20]
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
        rating_qs = UserRating.objects.filter(user=user)
        if profile:
            rating_qs = rating_qs.filter(profile=profile)
        rated_items = rating_qs.order_by('-updated_at')[:20]
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

    def get_seed_attribution(self, user, profile, tmdb_id, media_type):
        """
        Determines the precise, human-friendly reason prefix for a recommendation seed title:
        - 5-Star Rating: 'Because You Loved'
        - 4-Star Rating: 'Because You Liked'
        - 3-Star Rating: 'Because You Rated'
        - Actual Stream on Filvora: 'Because You Watched'
        - Library/Watchlist: "Because It's in Your Watchlist"
        """
        if not user or not user.is_authenticated:
            return "Recommended For You"

        # 1. Check user rating first
        rating_qs = UserRating.objects.filter(user=user, tmdb_id=tmdb_id, media_type=media_type)
        if profile:
            rating_qs = rating_qs.filter(profile=profile)
        user_rating = rating_qs.first()

        # 2. Check actual stream on Filvora
        progress_qs = WatchProgress.objects.filter(user=user, tmdb_id=tmdb_id, media_type=media_type)
        if profile:
            progress_qs = progress_qs.filter(profile=profile)
        has_watched = (
            progress_qs.filter(completed=True).exists() or
            progress_qs.filter(position_seconds__gt=30).exists()
        )

        if user_rating:
            if user_rating.score >= 5:
                return "Because You Loved"
            elif user_rating.score == 4:
                return "Because You Liked"
            elif user_rating.score == 3:
                return "Because You Rated"

        if has_watched:
            return "Because You Watched"

        # 3. Check library
        lib_qs = LibraryItem.objects.filter(user=user, tmdb_id=tmdb_id, media_type=media_type)
        if profile:
            lib_qs = lib_qs.filter(profile=profile)
        if lib_qs.exists():
            return "Because It's in Your Watchlist"

        return "Because You Liked"

    def _get_franchise_identifiers(self, tmdb_id, media_type, details=None):
        """
        Extracts collection ID and normalized franchise title prefixes.
        Used to prevent duplicate rails for sequels/prequels in the same franchise.
        """
        keys = set()
        if media_type != 'movie':
            keys.add(f"tv_{tmdb_id}")
            return keys

        if not details:
            try:
                details = self.client.get_movie_details(tmdb_id) or {}
            except Exception:
                details = {}

        # 1. Check official TMDB Collection
        coll = details.get('belongs_to_collection')
        if coll and isinstance(coll, dict) and coll.get('id'):
            keys.add(f"coll_{coll.get('id')}")

        # 2. Check title prefix (e.g., 'Spider-Man: Across the Spider-Verse' -> 'root_spider-man')
        title = (details.get('title') or '').strip()
        if title:
            # Strip subtitles following ':', '-', 'Part', 'Chapter', etc.
            raw_prefix = title.split(':')[0].split(' - ')[0].strip().lower()
            raw_prefix = re.sub(r'[\d\W]+$', '', raw_prefix).strip()
            if len(raw_prefix) >= 4 and raw_prefix not in {'the', 'a', 'an', 'movie'}:
                keys.add(f"root_{raw_prefix}")

        if not keys:
            keys.add(f"item_{tmdb_id}")

        return keys

    def _get_collection_parts_recs(self, details, tid, exclude_keys, global_seen_ids):
        """
        If a movie belongs to an official TMDB collection, fetches and returns
        any unstreamed, unrated sequels/prequels to prioritize at the head of recommendations.
        """
        parts_recs = []
        coll = details.get('belongs_to_collection')
        if coll and isinstance(coll, dict) and coll.get('id'):
            try:
                coll_data = self.client.get_collection(coll.get('id'))
                if coll_data and 'parts' in coll_data:
                    for part in coll_data['parts']:
                        part_id = part.get('id')
                        if not part_id or part_id == tid:
                            continue
                        if ('movie', part_id) in exclude_keys:
                            continue
                        if part_id in global_seen_ids:
                            continue
                        part_copy = dict(part)
                        part_copy['media_type'] = 'movie'
                        parts_recs.append(part_copy)
            except Exception:
                pass
        return parts_recs

    def get_contextual_rails(self, user, profile=None, max_rails=2):
        """
        Returns multiple distinct contextual recommendation rails based on user's top rated/watched titles.
        Ensures diverse seed titles, franchise sequel deduplication, accurate attribution prefixes ('Loved' vs 'Watched'),
        and eliminates duplicates across rails.
        """
        if not user or not user.is_authenticated:
            return []

        # Gather user's rated & completed items to avoid recommending already consumed content
        exclude_keys = set()

        rating_qs = UserRating.objects.filter(user=user)
        if profile:
            rating_qs = rating_qs.filter(profile=profile)
        for r in rating_qs.values('media_type', 'tmdb_id'):
            exclude_keys.add((r['media_type'], r['tmdb_id']))
            exclude_keys.add(('movie', r['tmdb_id']))
            exclude_keys.add(('tv', r['tmdb_id']))

        progress_qs = WatchProgress.objects.filter(user=user)
        if profile:
            progress_qs = progress_qs.filter(profile=profile)
        for p in progress_qs.filter(Q(completed=True) | Q(position_seconds__gt=300)).values('media_type', 'tmdb_id'):
            exclude_keys.add((p['media_type'], p['tmdb_id']))
            exclude_keys.add(('movie', p['tmdb_id']))
            exclude_keys.add(('tv', p['tmdb_id']))

        # Collect candidate seeds from ratings (score >= 4) and watch history (completed or position > 30)
        candidate_seeds = []
        seen_seeds = set()

        # Priority A: 4-5 star ratings
        for r in rating_qs.filter(score__gte=4).order_by('-updated_at')[:12]:
            key = (r.media_type, r.tmdb_id)
            if key not in seen_seeds:
                seen_seeds.add(key)
                candidate_seeds.append({
                    'media_type': r.media_type,
                    'tmdb_id': r.tmdb_id,
                })

        # Priority B: Streamed watch history
        for p in progress_qs.filter(Q(completed=True) | Q(position_seconds__gt=30)).order_by('-updated_at')[:12]:
            key = (p.media_type, p.tmdb_id)
            if key not in seen_seeds:
                seen_seeds.add(key)
                candidate_seeds.append({
                    'media_type': p.media_type,
                    'tmdb_id': p.tmdb_id,
                })

        # Priority C: Library items fallback
        if not candidate_seeds:
            lib_qs = LibraryItem.objects.filter(user=user)
            if profile:
                lib_qs = lib_qs.filter(profile=profile)
            for lib in lib_qs.order_by('-added_at')[:6]:
                key = (lib.media_type, lib.tmdb_id)
                if key not in seen_seeds:
                    seen_seeds.add(key)
                    candidate_seeds.append({
                        'media_type': lib.media_type,
                        'tmdb_id': lib.tmdb_id,
                    })

        if not candidate_seeds:
            return []

        rails = []
        global_recommended_ids = set()
        seen_franchise_identifiers = set()

        for seed in candidate_seeds:
            mtype = seed['media_type']
            tid = seed['tmdb_id']

            if mtype == 'movie':
                details = self.client.get_movie_details(tid)
                title = details.get('title', f"Movie {tid}")
            else:
                details = self.client.get_tv_details(tid)
                title = details.get('name', f"Series {tid}")

            # Deduplicate seeds belonging to the same franchise / sequel collection
            seed_franchise_keys = self._get_franchise_identifiers(tid, mtype, details=details)
            if seed_franchise_keys & seen_franchise_identifiers:
                continue

            # Prioritize unstreamed/unrated sequels/prequels from the same collection
            collection_parts = []
            if mtype == 'movie':
                collection_parts = self._get_collection_parts_recs(details, tid, exclude_keys, global_recommended_ids)

            recs = details.get('recommendations', {}).get('results', [])
            if not recs:
                genres = details.get('genres', [])
                if genres:
                    gid = genres[0].get('id') if isinstance(genres[0], dict) else genres[0]
                    recs = self.client.discover_content(media_type=mtype, genre_id=gid, min_rating=7.0)

            candidate_pool = collection_parts + recs

            # Filter out seed itself, already rated/watched items, and duplicates across rails
            filtered_recs = []
            for item in candidate_pool:
                item_id = item.get('id') or item.get('tmdb_id')
                item_mtype = item.get('media_type', mtype)
                if not item_id:
                    continue
                if item_id == tid:
                    continue
                if (item_mtype, item_id) in exclude_keys:
                    continue
                if item_id in global_recommended_ids:
                    continue

                filtered_recs.append(item)
                global_recommended_ids.add(item_id)
                if len(filtered_recs) >= 10:
                    break

            if filtered_recs:
                seen_franchise_identifiers.update(seed_franchise_keys)
                reason_prefix = self.get_seed_attribution(user, profile, tid, mtype)
                rails.append({
                    'title': title,
                    'reason_prefix': reason_prefix,
                    'media_type': mtype,
                    'tmdb_id': tid,
                    'items': filtered_recs,
                })

            if len(rails) >= max_rails:
                break

        return rails

    def get_because_you_watched(self, user, profile=None):
        """Returns recommendations based on the user's latest watched/rated title (100% backward compatible)."""
        rails = self.get_contextual_rails(user, profile=profile, max_rails=1)
        if rails:
            return rails[0]
        return None

    def get_personalized_recommendations(self, user, limit=12, profile=None):
        """Returns deterministic curated recommendations blended across user's top affinity genres & favorites."""
        if not user or not user.is_authenticated:
            return self.client.get_top_rated_movies()[:limit]

        # Gather user's already consumed / rated items to filter out
        exclude_keys = set()

        rating_qs = UserRating.objects.filter(user=user)
        if profile:
            rating_qs = rating_qs.filter(profile=profile)
        for r in rating_qs.values('media_type', 'tmdb_id'):
            exclude_keys.add((r['media_type'], r['tmdb_id']))
            exclude_keys.add(('movie', r['tmdb_id']))
            exclude_keys.add(('tv', r['tmdb_id']))

        progress_qs = WatchProgress.objects.filter(user=user)
        if profile:
            progress_qs = progress_qs.filter(profile=profile)
        for p in progress_qs.filter(Q(completed=True) | Q(position_seconds__gt=300)).values('media_type', 'tmdb_id'):
            exclude_keys.add((p['media_type'], p['tmdb_id']))
            exclude_keys.add(('movie', p['tmdb_id']))
            exclude_keys.add(('tv', p['tmdb_id']))

        top_genres = self.get_user_affinity_genres(user, profile=profile)

        candidate_pools = []

        # 1. Pull recommendations from user's top 2 rated seeds
        top_seeds = rating_qs.filter(score__gte=4).order_by('-updated_at')[:2]
        for s in top_seeds:
            if s.media_type == 'movie':
                s_details = self.client.get_movie_details(s.tmdb_id)
            else:
                s_details = self.client.get_tv_details(s.tmdb_id)
            recs = s_details.get('recommendations', {}).get('results', [])
            if recs:
                candidate_pools.append(recs)

        # 2. Pull discover content across top 2-3 affinity genres
        if top_genres:
            for gid in top_genres[:3]:
                genre_movies = self.client.discover_content(
                    media_type='movie',
                    genre_id=gid,
                    min_rating=7.0,
                    sort_by='vote_average.desc'
                )
                if genre_movies:
                    candidate_pools.append(genre_movies)

        # 3. Interleave candidate pools in round-robin fashion for balanced diversity
        blended = []
        seen_ids = set()

        if candidate_pools:
            max_depth = max(len(p) for p in candidate_pools)
            for depth in range(max_depth):
                for pool in candidate_pools:
                    if depth < len(pool):
                        item = pool[depth]
                        item_id = item.get('id') or item.get('tmdb_id')
                        mtype = item.get('media_type', 'movie')
                        if item_id and item_id not in seen_ids and (mtype, item_id) not in exclude_keys:
                            seen_ids.add(item_id)
                            blended.append(item)
                            if len(blended) >= limit:
                                break
                if len(blended) >= limit:
                    break

        if blended:
            return blended[:limit]

        # Fallback to top rated movies if no affinity signals or all were excluded
        top_rated = self.client.get_top_rated_movies()
        clean_fallback = [m for m in top_rated if (m.get('media_type', 'movie'), m.get('id')) not in exclude_keys]
        return clean_fallback[:limit] if clean_fallback else top_rated[:limit]

    def get_dedicated_recommendations(self, user, profile=None, media_filter='all'):
        """
        Builds comprehensive, multi-section personalized recommendations for the dedicated Recommendations Hub.
        Partitions recommendations into:
        - top_picks: Blended top recommendations across movies/series
        - ratings_rails: Dedicated contextual rails from user's 4-5 star ratings
        - history_rails: Dedicated contextual rails from user's streamed watch history
        - genre_rails: Curated discoveries from user's top affinity genres
        - stats: User personalization profile stats (rated count, streamed count, top genres)
        """
        genre_names_map = {
            28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
            99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
            27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
            10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
            10759: "Action & Adventure", 10762: "Kids", 10765: "Sci-Fi & Fantasy", 10768: "War & Politics"
        }

        if not user or not user.is_authenticated:
            top_movies = self.client.get_top_rated_movies() if media_filter != 'tv' else []
            top_series = self.client.get_top_rated_series() if media_filter != 'movie' else []
            blended = top_movies[:12] if media_filter == 'movie' else (top_series[:12] if media_filter == 'tv' else (top_movies[:8] + top_series[:8]))
            return {
                'has_signals': False,
                'top_picks': blended,
                'ratings_rails': [],
                'history_rails': [],
                'genre_rails': [],
                'stats': {'total_rated': 0, 'total_streamed': 0, 'top_genres': []}
            }

        # 1. User stats & signals
        rating_qs = UserRating.objects.filter(user=user)
        if profile:
            rating_qs = rating_qs.filter(profile=profile)
        total_rated = rating_qs.count()

        progress_qs = WatchProgress.objects.filter(user=user)
        if profile:
            progress_qs = progress_qs.filter(profile=profile)
        total_streamed = progress_qs.count()

        top_genre_ids = self.get_user_affinity_genres(user, profile=profile)
        top_genre_names = [genre_names_map.get(gid, f"Genre {gid}") for gid in top_genre_ids if gid in genre_names_map]

        has_signals = (total_rated > 0) or (total_streamed > 0)

        # Gather user's consumed / rated items to exclude
        exclude_keys = set()
        for r in rating_qs.values('media_type', 'tmdb_id'):
            exclude_keys.add((r['media_type'], r['tmdb_id']))
            exclude_keys.add(('movie', r['tmdb_id']))
            exclude_keys.add(('tv', r['tmdb_id']))

        for p in progress_qs.filter(Q(completed=True) | Q(position_seconds__gt=300)).values('media_type', 'tmdb_id'):
            exclude_keys.add((p['media_type'], p['tmdb_id']))
            exclude_keys.add(('movie', p['tmdb_id']))
            exclude_keys.add(('tv', p['tmdb_id']))

        global_seen_ids = set()

        def _matches_filter(item):
            if media_filter == 'all':
                return True
            mtype = item.get('media_type')
            if not mtype:
                mtype = 'movie' if 'title' in item else 'tv'
            return mtype == media_filter

        # 2. Ratings-driven Contextual Rails (4-5 stars)
        ratings_rails = []
        rated_seeds = list(rating_qs.filter(score__gte=4).order_by('-updated_at')[:12])
        rated_seed_keys = set()
        seen_ratings_franchise_keys = set()

        for r in rated_seeds:
            key = (r.media_type, r.tmdb_id)
            if key in rated_seed_keys:
                continue
            rated_seed_keys.add(key)

            if r.media_type == 'movie':
                details = self.client.get_movie_details(r.tmdb_id)
                title = details.get('title', f"Movie {r.tmdb_id}")
            else:
                details = self.client.get_tv_details(r.tmdb_id)
                title = details.get('name', f"Series {r.tmdb_id}")

            # Franchise & sequel seed deduplication
            franchise_keys = self._get_franchise_identifiers(r.tmdb_id, r.media_type, details=details)
            if franchise_keys & seen_ratings_franchise_keys:
                continue

            collection_parts = []
            if r.media_type == 'movie':
                collection_parts = self._get_collection_parts_recs(details, r.tmdb_id, exclude_keys, global_seen_ids)

            recs = details.get('recommendations', {}).get('results', [])
            if not recs:
                genres = details.get('genres', [])
                if genres:
                    gid = genres[0].get('id') if isinstance(genres[0], dict) else genres[0]
                    recs = self.client.discover_content(media_type=r.media_type, genre_id=gid, min_rating=7.0)

            candidate_pool = collection_parts + recs
            filtered = []
            for item in candidate_pool:
                item_id = item.get('id') or item.get('tmdb_id')
                item_mtype = item.get('media_type', r.media_type)
                if not item_id or item_id == r.tmdb_id:
                    continue
                if (item_mtype, item_id) in exclude_keys or item_id in global_seen_ids:
                    continue
                if not _matches_filter(item):
                    continue

                filtered.append(item)
                global_seen_ids.add(item_id)
                if len(filtered) >= 10:
                    break

            if filtered:
                seen_ratings_franchise_keys.update(franchise_keys)
                reason_prefix = "Because You Loved" if r.score == 5 else "Because You Liked"
                ratings_rails.append({
                    'title': title,
                    'reason_prefix': reason_prefix,
                    'media_type': r.media_type,
                    'score': r.score,
                    'items': filtered
                })

            if len(ratings_rails) >= 3:
                break

        # 3. Streamed History-driven Contextual Rails
        history_rails = []
        streamed_seeds = list(progress_qs.filter(Q(completed=True) | Q(position_seconds__gt=30)).order_by('-updated_at')[:12])
        streamed_seed_keys = set()
        seen_history_franchise_keys = set(seen_ratings_franchise_keys)

        for p in streamed_seeds:
            key = (p.media_type, p.tmdb_id)
            if key in rated_seed_keys or key in streamed_seed_keys:
                continue
            streamed_seed_keys.add(key)

            if p.media_type == 'movie':
                details = self.client.get_movie_details(p.tmdb_id)
                title = details.get('title', f"Movie {p.tmdb_id}")
            else:
                details = self.client.get_tv_details(p.tmdb_id)
                title = details.get('name', f"Series {p.tmdb_id}")

            franchise_keys = self._get_franchise_identifiers(p.tmdb_id, p.media_type, details=details)
            if franchise_keys & seen_history_franchise_keys:
                continue

            collection_parts = []
            if p.media_type == 'movie':
                collection_parts = self._get_collection_parts_recs(details, p.tmdb_id, exclude_keys, global_seen_ids)

            recs = details.get('recommendations', {}).get('results', [])
            if not recs:
                genres = details.get('genres', [])
                if genres:
                    gid = genres[0].get('id') if isinstance(genres[0], dict) else genres[0]
                    recs = self.client.discover_content(media_type=p.media_type, genre_id=gid, min_rating=7.0)

            candidate_pool = collection_parts + recs
            filtered = []
            for item in candidate_pool:
                item_id = item.get('id') or item.get('tmdb_id')
                item_mtype = item.get('media_type', p.media_type)
                if not item_id or item_id == p.tmdb_id:
                    continue
                if (item_mtype, item_id) in exclude_keys or item_id in global_seen_ids:
                    continue
                if not _matches_filter(item):
                    continue

                filtered.append(item)
                global_seen_ids.add(item_id)
                if len(filtered) >= 10:
                    break

            if filtered:
                seen_history_franchise_keys.update(franchise_keys)
                history_rails.append({
                    'title': title,
                    'reason_prefix': "Because You Watched",
                    'media_type': p.media_type,
                    'items': filtered
                })

            if len(history_rails) >= 3:
                break

        # 4. Top Picks Grid (blended multi-genre + seed picks)
        top_picks = []
        candidate_pools = []
        for s in rated_seeds[:2]:
            s_details = self.client.get_movie_details(s.tmdb_id) if s.media_type == 'movie' else self.client.get_tv_details(s.tmdb_id)
            s_recs = s_details.get('recommendations', {}).get('results', [])
            if s_recs:
                candidate_pools.append(s_recs)

        if top_genre_ids:
            for gid in top_genre_ids[:3]:
                if media_filter in ['all', 'movie']:
                    m_recs = self.client.discover_content(media_type='movie', genre_id=gid, min_rating=7.0)
                    if m_recs:
                        candidate_pools.append(m_recs)
                if media_filter in ['all', 'tv']:
                    tv_recs = self.client.discover_content(media_type='tv', genre_id=gid, min_rating=7.0)
                    if tv_recs:
                        candidate_pools.append(tv_recs)

        if candidate_pools:
            max_depth = max(len(p) for p in candidate_pools)
            for depth in range(max_depth):
                for pool in candidate_pools:
                    if depth < len(pool):
                        item = pool[depth]
                        item_id = item.get('id') or item.get('tmdb_id')
                        item_mtype = item.get('media_type', 'movie')
                        if item_id and item_id not in global_seen_ids and (item_mtype, item_id) not in exclude_keys and _matches_filter(item):
                            global_seen_ids.add(item_id)
                            top_picks.append(item)
                            if len(top_picks) >= 18:
                                break
                if len(top_picks) >= 18:
                    break

        if not top_picks:
            fallback = self.client.get_top_rated_movies() if media_filter == 'movie' else (self.client.get_top_rated_series() if media_filter == 'tv' else (self.client.get_top_rated_movies()[:9] + self.client.get_top_rated_series()[:9]))
            top_picks = [m for m in fallback if (m.get('media_type', 'movie'), m.get('id')) not in exclude_keys][:18]

        # 5. Top Genre Universes
        genre_rails = []
        if top_genre_ids:
            for gid in top_genre_ids[:2]:
                g_name = genre_names_map.get(gid, "Popular")
                g_items = []
                if media_filter in ['all', 'movie']:
                    g_items.extend(self.client.discover_content(media_type='movie', genre_id=gid, min_rating=7.0)[:8])
                if media_filter in ['all', 'tv']:
                    g_items.extend(self.client.discover_content(media_type='tv', genre_id=gid, min_rating=7.0)[:8])

                clean_g_items = [i for i in g_items if (i.get('media_type', 'movie'), i.get('id')) not in exclude_keys and _matches_filter(i)]
                if clean_g_items:
                    genre_rails.append({
                        'genre_id': gid,
                        'genre_name': g_name,
                        'items': clean_g_items[:10]
                    })

        return {
            'has_signals': has_signals,
            'top_picks': top_picks,
            'ratings_rails': ratings_rails,
            'history_rails': history_rails,
            'genre_rails': genre_rails,
            'stats': {
                'total_rated': total_rated,
                'total_streamed': total_streamed,
                'top_genres': top_genre_names
            }
        }
