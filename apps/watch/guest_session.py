import time

GUEST_PROGRESS_SESSION_KEY = 'guest_watch_progress'
GUEST_SERVER_SESSION_KEY = 'guest_server_prefs'
GUEST_PROGRESS_TTL_SECONDS = 12 * 3600  # 12 hours temporary session window (not saved permanently)
GUEST_MAX_PROGRESS_ITEMS = 6
GUEST_MAX_SERVER_PREFS = 10


def _clean_int(value):
    if value is None or str(value).strip() == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _title_key(media_type: str, tmdb_id: int) -> str:
    return f"{media_type}:{int(tmdb_id)}"


def _server_key(media_type: str, tmdb_id: int, season=None, episode=None) -> str:
    return f"{media_type}:{int(tmdb_id)}:{_clean_int(season) or 0}:{_clean_int(episode) or 0}"


def get_guest_progress_map(request) -> dict:
    """Returns non-expired temporary currently-playing map ordered newest-first."""
    raw = request.session.get(GUEST_PROGRESS_SESSION_KEY)
    if not isinstance(raw, dict) or not raw:
        return {}

    now = time.time()
    fresh = []
    pruned = False

    for key, entry in raw.items():
        if not isinstance(entry, dict):
            pruned = True
            continue
        updated_at = float(entry.get('updated_at') or 0)
        if (now - updated_at) > GUEST_PROGRESS_TTL_SECONDS or entry.get('completed'):
            pruned = True
            continue
        if float(entry.get('position_seconds') or 0) < 15:
            pruned = True
            continue
        fresh.append((key, entry))

    fresh.sort(key=lambda kv: float(kv[1].get('updated_at') or 0), reverse=True)
    if len(fresh) > GUEST_MAX_PROGRESS_ITEMS:
        fresh = fresh[:GUEST_MAX_PROGRESS_ITEMS]
        pruned = True

    cleaned = dict(fresh)
    if pruned:
        if cleaned:
            request.session[GUEST_PROGRESS_SESSION_KEY] = cleaned
        else:
            request.session.pop(GUEST_PROGRESS_SESSION_KEY, None)
        request.session.modified = True

    return cleaned


def upsert_guest_progress(
    request,
    tmdb_id: int,
    media_type: str,
    position_seconds: float,
    duration_seconds: float,
    season=None,
    episode=None,
    completed: bool = False,
) -> int:
    """Stores temporary currently-playing progress in session; deletes it if completed."""
    current = dict(get_guest_progress_map(request))
    key = _title_key(media_type, tmdb_id)

    if completed:
        if key in current:
            del current[key]
            if current:
                request.session[GUEST_PROGRESS_SESSION_KEY] = current
            else:
                request.session.pop(GUEST_PROGRESS_SESSION_KEY, None)
            request.session.modified = True
        return 100

    pct = 0
    if duration_seconds > 0:
        pct = min(100, round((position_seconds / duration_seconds) * 100))

    s_num = _clean_int(season) if media_type == 'tv' else None
    ep_num = _clean_int(episode) if media_type == 'tv' else None

    current[key] = {
        'tmdb_id': int(tmdb_id),
        'media_type': media_type,
        'season': s_num,
        'episode': ep_num,
        'position_seconds': float(position_seconds),
        'duration_seconds': float(duration_seconds),
        'progress_percentage': pct,
        'completed': False,
        'updated_at': time.time(),
    }

    sorted_items = sorted(
        current.items(),
        key=lambda kv: float(kv[1].get('updated_at') or 0),
        reverse=True,
    )[:GUEST_MAX_PROGRESS_ITEMS]

    request.session[GUEST_PROGRESS_SESSION_KEY] = dict(sorted_items)
    request.session.modified = True
    return pct


def remove_guest_progress(request, tmdb_id, media_type: str = 'movie', season=None, episode=None) -> bool:
    """Removes a temporary currently-playing entry from the guest session."""
    current = dict(get_guest_progress_map(request))
    key = _title_key(media_type, int(tmdb_id))
    entry = current.get(key)
    if not entry:
        return False

    s_num = _clean_int(season)
    ep_num = _clean_int(episode)
    if media_type == 'tv' and (s_num is not None or ep_num is not None):
        if s_num is not None and entry.get('season') != s_num:
            return False
        if ep_num is not None and entry.get('episode') != ep_num:
            return False

    del current[key]
    if current:
        request.session[GUEST_PROGRESS_SESSION_KEY] = current
    else:
        request.session.pop(GUEST_PROGRESS_SESSION_KEY, None)
    request.session.modified = True
    return True


def get_guest_resume_item(request, tmdb_id: int, media_type: str, season=None, episode=None):
    """Returns temporary guest resume entry for exact movie or episode if >= 30s."""
    current = get_guest_progress_map(request)
    entry = current.get(_title_key(media_type, tmdb_id))
    if not entry:
        return None
    if media_type == 'tv':
        if entry.get('season') != _clean_int(season) or entry.get('episode') != _clean_int(episode):
            return None
    if float(entry.get('position_seconds') or 0) < 30:
        return None
    return entry


def get_guest_server_pref(request, tmdb_id: int, media_type: str, season=None, episode=None):
    prefs = request.session.get(GUEST_SERVER_SESSION_KEY)
    if not isinstance(prefs, dict):
        return None
    return prefs.get(_server_key(media_type, tmdb_id, season, episode))


def set_guest_server_pref(request, tmdb_id: int, media_type: str, provider_id: str, season=None, episode=None):
    if not provider_id:
        return
    prefs = dict(request.session.get(GUEST_SERVER_SESSION_KEY) or {})
    key = _server_key(media_type, tmdb_id, season, episode)
    prefs[key] = provider_id
    if len(prefs) > GUEST_MAX_SERVER_PREFS:
        keys = list(prefs.keys())[-GUEST_MAX_SERVER_PREFS:]
        prefs = {k: prefs[k] for k in keys}
    request.session[GUEST_SERVER_SESSION_KEY] = prefs
    request.session.modified = True
