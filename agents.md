# 🤖 AGENTS.MD — Filvora Engineering Master Specification & Session Continuation Guide

> **Purpose of this Document**:  
> This file is the primary context and handover document for any AI agent or software engineer continuing work on the **Filvora** codebase. It documents the exact current state of the application, architecture, conventions, active background processes, database models, frontend interaction patterns, known quirks, and upcoming roadmap items.

---

## 1. System Environment & Runtime State

### 1.1 Local Environment
- **Operating System**: Windows (PowerShell)
- **Project Root**: `D:\Om\Projects\Filvora`
- **Python Virtualenv**: `D:\Om\Projects\Filvora\venv`
  - Python Executable: `.\venv\Scripts\python.exe`
- **Django Version**: 5.2+ (Django REST Framework, Requests, Python-Dotenv)
- **Active Server Task**: 
  - Django Development Server is active on **`http://127.0.0.1:8000/`**
  - Command: `.\venv\Scripts\python.exe manage.py runserver`
  - All routes (`/`, `/movies/`, `/series/`, `/library/`, `/search/`) return `200 OK`.

---

## 2. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, global search, and utility helpers
│   ├── catalog/               # Movie/Series browse, detail, and season/episode endpoints
│   ├── playback/              # Video player view, provider registry, and server switching
│   ├── library/               # Watchlist models, HTMX toggle views, and My List
│   └── accounts/              # User authentication (Login, Register, Logout)
├── config/
│   ├── settings.py            # Django configuration and environment variables
│   ├── urls.py                # Main URL routing definitions
│   ├── wsgi.py / asgi.py      # WSGI/ASGI application gateways
│   └── tmdb.py                # TMDB API client with memory/file caching
├── static/
│   ├── css/
│   │   ├── main.css           # Glassmorphism, animations, and rail scroll styles
│   │   └── videojs/           # Video.js player themes and stylesheets
│   └── js/
│       ├── main.js            # Rail drag-scroll, keyboard shortcuts, and toast engine
│       └── videojs/           # Video.js core and HLS libraries
└── templates/
    ├── base.html              # Base layout with Plus Jakarta Sans & mobile bottom nav
    ├── includes/
    │   └── navbar.html        # Glassmorphic top bar with v2.0 branding & live search
    ├── home/
    │   └── index.html         # Homepage with Hero billboard and category rails
    ├── catalog/
    │   ├── movie_browse.html  # Movies grid with v2.0 hover overlays
    │   ├── movie_detail.html  # Movie synopsis, cast, and recommendations
    │   ├── series_browse.html # TV series grid
    │   ├── series_detail.html # Series synopsis, seasons, and episode list
    │   ├── search_results.html# Full search results grid
    │   └── partials/          # HTMX search suggestions and episode list partials
    ├── playback/
    │   └── watch.html         # Fullscreen video player with server switcher
    ├── library/
    │   └── list.html          # My List watchlist with category filter tabs
    └── accounts/
        ├── login.html         # User sign in form
        └── register.html      # User registration form
```

---

## 3. Current Implementation Status

### 3.1 Metadata & TMDB Integration (`config/tmdb.py`)
- **TMDB API Client**: Encapsulates endpoints for:
  - `get_trending(media_type, time_window)`
  - `get_popular_movies()`, `get_top_rated_movies()`, `get_popular_series()`
  - `get_movie_details(tmdb_id, append_to_response='credits,recommendations,similar')`
  - `get_series_details(tmdb_id, append_to_response='credits,recommendations')`
  - `get_season_details(series_id, season_number)`
  - `search_multi(query)`
- **Error Handling**: Graceful fallback with try/except wrappers returning empty datasets when TMDB experiences network dropouts or timeouts.

### 3.2 Playback Engine (`apps/playback/`)
- **Multi-Server Provider Engine** (`apps/playback/views.py`):
  - Configurable server array supporting primary and secondary streaming nodes (`Vidsrc`, `SuperEmbed`, `2Embed`, `EmbedSoap`, etc.).
  - Direct Video.js playback for `.m3u8` / `.mp4` sources and responsive iframe sandbox for embed streams.
  - Server Switcher replaces the `?server=<id>` query parameter in-place via `window.location.replace` to prevent cluttering browser history.
  - Automatic **Next Episode** URL generator for TV series (`/watch/tv/<id>/<season>/<ep+1>/`).

### 3.3 Playback Progress Tracking & Continue Watching (`apps/core/` & `apps/playback/`)
- **Progress Model** (`apps/playback/models.py` - `WatchProgress`):
  - Fields: `user`, `tmdb_id`, `media_type`, `position_seconds`, `duration_seconds`, `season`, `episode`, `completed`, `updated_at`.
- **Heartbeat Beacon**: The player sends progress updates every 15 seconds via `navigator.sendBeacon('/progress/save/', blob)`.
- **Continue Watching Rail**:
  - Injected on the homepage (`apps/core/views.py`).
  - Displays movie/episode cards with real-time percentage progress bars and one-click instant resume.

### 3.4 Library & Watchlist (`apps/library/`)
- **Model** (`apps/library/models.py` - `LibraryItem`):
  - Fields: `user`, `tmdb_id`, `media_type`, `created_at`.
- **HTMX Dynamic Toggling**:
  - Endpoint: `POST /library/toggle/` with payload `{"tmdb_id": "...", "media_type": "...", "variant": "card"|"hero"|"default"}`.
  - If `variant == 'card'`: Returns a compact circular pill button (`w-8 h-8 rounded-full`).
  - If `variant == 'default'`: Returns full CTA button (`Saved in My List` / `Add to My List`).
- **Context Injection**: `user_saved_ids = set(...)` is injected across `HomeView`, `movie_browse`, `series_browse`, and `movie_detail` to eliminate N+1 queries when evaluating saved states.

### 3.5 Filvora v2.0 UI & UX Overhaul
- **Branding**: `v2.0` badge on Navbar, player overlay, footer, and page titles.
- **Typography**: Google Font **Plus Jakarta Sans** loaded in `templates/base.html`.
- **Horizontal Rails Carousel**:
  - Smooth left (`<`) and right (`>`) arrow scroll buttons.
  - Mouse click-and-drag horizontal grab scrolling (`.rail-track.is-dragging`).
  - Standard vertical page scrolling preserved during mouse-wheel scroll over rails.
- **Card Hover Overlays**:
  - Top: TMDB Rating badge (`⭐ 8.4`), Quality badge (`HD` / `TV-MA`).
  - Center: Large red play button that starts playback immediately upon clicking.
  - Bottom: High-contrast white action play button (`M8 5v14l11-7z` solid triangle), async Watchlist button, and More Info (`ℹ️`) button.
- **Mobile Bottom Navigation Bar**: Fixed glassmorphic navigation bar on mobile viewports (`md:hidden`) with Home, Movies, Series, My List, and Search icons.
- **Keyboard Shortcuts**:
  - Global `/` focuses and selects the search input.
  - Global `?` or `Shift + /` toggles the Keyboard Shortcuts Modal.
  - Video Player: `Space`/`K` (Play/Pause), `F` (Fullscreen), `M` (Mute), `←`/`→` (Seek 10s), `Esc` (Close dialogs).
- **Toast Notifications**: Built-in JavaScript toast notification system triggered on HTMX watchlist events.

---

## 4. Key Conventions & Quirks to Remember

1. **Play Icon SVGs**:
   - **DO NOT** use Heroicons `play-circle` paths (`M10 18a8 8 0...`) inside round buttons because it creates a double-circle / target distortion.
   - **ALWAYS** use the clean solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-black translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
2. **HTMX Click Event Propagation on Cards**:
   - Cards are wrapped in clickable anchor tags.
   - Any nested action buttons (Watchlist, More Info) must include:
     `onclick="event.preventDefault(); event.stopPropagation();"`
     to prevent triggering parent link navigation.
3. **HTMX CSRF Header**:
   - `templates/base.html` configures global CSRF tokens for all HTMX requests:
     ```javascript
     document.addEventListener('htmx:configRequest', (event) => {
         event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
     });
     ```
4. **Video Player History Management**:
   - When changing servers in `templates/playback/watch.html`, use `window.location.replace('?server=' + this.value)` instead of `window.location.href = ...` so that clicking the browser "Back" button returns the user directly to the movie details page rather than looping through server selections.

---

## 5. Route Map Reference

| Route | View Function | App | Template |
|---|---|---|---|
| `/` | `HomeView` | `apps.core` | `templates/home/index.html` |
| `/movies/` | `movie_browse` | `apps.catalog` | `templates/catalog/movie_browse.html` |
| `/movies/<id>/` | `movie_detail` | `apps.catalog` | `templates/catalog/movie_detail.html` |
| `/series/` | `series_browse` | `apps.catalog` | `templates/catalog/series_browse.html` |
| `/series/<id>/` | `series_detail` | `apps.catalog` | `templates/catalog/series_detail.html` |
| `/series/<id>/season/<num>/` | `season_episodes` | `apps.catalog` | `templates/catalog/partials/episode_list.html` |
| `/watch/movie/<id>/` | `watch_movie` | `apps.playback` | `templates/playback/watch.html` |
| `/watch/tv/<id>/<s_num>/<ep_num>/` | `watch_episode` | `apps.playback` | `templates/playback/watch.html` |
| `/search/` | `search_results` | `apps.catalog` | `templates/catalog/search_results.html` |
| `/search/suggest/` | `search_suggestions`| `apps.catalog` | `templates/catalog/partials/search_suggestions.html` |
| `/library/` | `library_list` | `apps.library` | `templates/library/list.html` |
| `/library/toggle/` | `toggle_item` | `apps.library` | HTMX Fragment |
| `/progress/save/` | `save_progress` | `apps.playback` | JSON Response (Beacon) |
| `/accounts/login/` | `login_view` | `apps.accounts` | `templates/accounts/login.html` |
| `/accounts/register/` | `register_view` | `apps.accounts` | `templates/accounts/register.html` |
| `/accounts/logout/` | `logout_view` | `apps.accounts` | Redirect to `/` |

---

## 6. How to Continue Development & Next Tasks

When picking up the next development session, consider these prioritized feature enhancements:

1. **Genre Explorer & Filter View**:
   - Add a dedicated `/genres/` or filter dropdown on `/movies/` and `/series/` to filter by TMDB Genre ID, release year, and minimum rating.
2. **User Profiles System**:
   - Allow users to create multiple profiles (e.g. "Main", "Kids", "Guest") under a single account, each maintaining independent watchlists and continue-watching history.
3. **Custom Playlists & Collections**:
   - Expand `apps.library` to support custom user-created lists (e.g. "Weekend Sci-Fi Marathon", "Oscar Winners").
4. **Enhanced Video.js Direct HLS Extraction**:
   - Add support for subtitle track (`.vtt`) auto-loading and audio track switching when direct streams are available.
5. **Automated Unit & Integration Tests**:
   - Add test suites in `apps/*/tests.py` covering TMDB mock responses, HTMX library toggle endpoints, and watch progress beacons.

---

## 7. Useful Command Shortcuts for Agents

```powershell
# Run Django Development Server
.\venv\Scripts\python.exe manage.py runserver

# Run Migrations
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate

# Test Routes via PowerShell
irm http://127.0.0.1:8000/ | Out-Null; Write-Host "Server Active 200"

# Open Django Shell
.\venv\Scripts\python.exe manage.py shell
```
