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
  - All routes (`/`, `/movies/`, `/series/`, `/library/`, `/search/`, `/progress/save/`, `/progress/remove/`) return `200 OK`.

---

## 2. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, global search, and continue watching context
│   ├── catalog/               # Movie/Series browse, detail, and season/episode endpoints
│   ├── playback/              # Video player view, provider registry, and server switching
│   ├── watch/                 # WatchProgress model and progress save/remove beacon endpoints
│   ├── tmdb/                  # TMDB API client with curl/requests fallback, caching & age ratings
│   ├── library/               # Watchlist models, HTMX toggle views, and My List
│   └── accounts/              # User authentication (Login, Register, Logout)
├── config/
│   ├── settings.py            # Django configuration and environment variables
│   ├── urls.py                # Main URL routing definitions
│   └── wsgi.py / asgi.py      # WSGI/ASGI application gateways
├── static/
│   ├── css/
│   │   ├── main.css           # Glassmorphism, animations, rail scroll styles & anti-clipping headroom
│   │   └── videojs/           # Video.js player themes and stylesheets
│   └── js/
│       ├── main.js            # Rail drag-scroll, keyboard shortcuts, and toast feedback engine
│       └── videojs/           # Video.js core and HLS libraries
└── templates/
    ├── base.html              # Base layout with Plus Jakarta Sans, navbar, footer & mobile bottom nav
    ├── includes/
    │   └── navbar.html        # Glassmorphic top bar with v2.0 branding, search & keyboard hint
    ├── home/
    │   └── index.html         # Homepage with Hero billboard and category rails
    ├── catalog/
    │   ├── movie_browse.html  # Movies grid with v2.0 hover overlays & age ratings
    │   ├── movie_detail.html  # Movie synopsis, cast, and recommendations
    │   ├── series_browse.html # TV series grid
    │   ├── series_detail.html # Series synopsis, seasons, and episode list
    │   ├── search_results.html# Full search results grid with age ratings
    │   └── partials/          # HTMX search suggestions and episode list partials
    ├── playback/
    │   └── watch.html         # Fullscreen video player with multi-server switcher
    ├── library/
    │   └── list.html          # My List watchlist with category filter tabs
    └── accounts/
        ├── login.html         # User sign in form
        └── register.html      # User registration form
```

---

## 3. Current Implementation Status

### 3.1 Metadata & Age Ratings Engine (`apps/tmdb/client.py`)
- **TMDB API Client**: Encapsulates endpoints with dual-mode execution (Windows Schannel `curl.exe` with `--ssl-no-revoke` and `requests` fallback) and in-memory TTL caching.
- **Content Certification & Age Ratings**:
  - **Movies**: Queries TMDB `release_dates` (`append_to_response=release_dates`) to extract official film certifications (e.g., `PG-13`, `R`, `PG`, `G`, `NC-17`, `18+`).
  - **TV Series**: Queries TMDB `content_ratings` (`append_to_response=content_ratings`) to extract official TV ratings (e.g., `TV-MA`, `TV-14`, `TV-PG`, `TV-G`, `TV-Y7`).
  - **List & Search Heuristics**: Automatic genre and adult-flag fallback (`_attach_age_rating`) ensures all card grids and search suggestions display consistent badges.
- **Error Handling**: Graceful fallback returning mock data and empty datasets when TMDB experiences network dropouts or timeouts.

### 3.2 Playback Engine (`apps/playback/`)
- **Multi-Server Provider Engine** (`apps/playback/views.py`):
  - Configurable server array supporting primary and secondary streaming nodes (`Vidsrc`, `SuperEmbed`, `2Embed`, `EmbedSoap`, etc.).
  - Direct Video.js playback for `.m3u8` / `.mp4` sources and responsive iframe sandbox for embed streams.
  - Server Switcher replaces the `?server=<id>` query parameter in-place via `window.location.replace` to prevent cluttering browser history.
  - Automatic **Next Episode** URL generator for TV series (`/watch/tv/<id>/<season>/<ep+1>/`).

### 3.3 Playback Progress Tracking & Continue Watching (`apps/watch/` & `apps/core/`)
- **Progress Model** (`apps/watch/models.py` - `WatchProgress`):
  - Fields: `user`, `tmdb_id`, `media_type`, `position_seconds`, `duration_seconds`, `season`, `episode`, `completed`, `updated_at`.
- **Heartbeat Beacon**: The player sends progress updates every 15 seconds via `navigator.sendBeacon('/progress/save/', blob)`.
- **Continue Watching Rail & In-Place Removal**:
  - Injected on the homepage (`apps/core/views.py`).
  - Displays movie/episode cards with real-time percentage progress bars and one-click instant resume.
  - **One-Click Remove Button (`×`)**: Endpoint `POST /progress/remove/` deletes `WatchProgress` records via HTMX in-place (`hx-swap="outerHTML swap:300ms"`), immediately removing the card with toast notification.

### 3.4 Library & Watchlist (`apps/library/`)
- **Model** (`apps/library/models.py` - `LibraryItem`):
  - Fields: `user`, `tmdb_id`, `media_type`, `created_at`.
- **HTMX Dynamic Toggling**:
  - Endpoint: `POST /library/toggle/` with payload `{"tmdb_id": "...", "media_type": "...", "variant": "card"|"hero"|"default"}`.
  - If `variant == 'card'`: Returns a compact circular pill button (`w-8 h-8 rounded-full`).
  - If `variant == 'default'`: Returns full CTA button (`Saved in My List` / `Add to My List`).
- **Context Injection**: `user_saved_ids = set(...)` is injected across views to eliminate N+1 queries.

### 3.5 Filvora v2.0 UI & UX Overhaul
- **Branding**: `v2.0` badge on Navbar, player overlay, footer, and page titles.
- **Typography**: Google Font **Plus Jakarta Sans** loaded in `templates/base.html`.
- **Horizontal Rails Carousel & Anti-Clipping**:
  - `.rail-track` has 24px of top and bottom headroom padding (`py-6 px-2 -my-3` / `padding: 1.5rem !important`) preventing cards scaling up on hover from clipping at the top.
  - Smooth left (`<`) and right (`>`) arrow scroll buttons.
  - Mouse click-and-drag horizontal grab scrolling (`.rail-track.is-dragging`).
  - Standard vertical mouse-wheel scrolling is preserved (no wheel interception).
- **Accurate Metadata Policy**:
  - Removed misleading placeholder badges (`4K Ultra HD`, `Dolby Atmos`, `HDR10+`, `5.1 Audio`) in favor of authentic `HD 1080p` and genuine TMDB star scores (`★ 8.4`).
- **Card Hover Overlays**:
  - Top: TMDB Rating badge (`⭐ 8.4`), Age Rating badge (`PG-13` / `TV-MA`), Quality badge (`HD`).
  - Center: Large red play button that starts playback immediately upon clicking.
  - Bottom: High-contrast white action play button (`M8 5v14l11-7z` solid triangle), async Watchlist button, and More Info (`ℹ️`) button.
- **Mobile Bottom Navigation Bar**: Fixed glassmorphic navigation bar on mobile viewports (`md:hidden`) with Home, Movies, Series, My List, and Search icons.
- **Keyboard Shortcuts**:
  - Global `/` focuses and selects the search input.
  - Global `?` or `Shift + /` toggles the Keyboard Shortcuts Modal.
  - Video Player: `Space`/`K` (Play/Pause), `F` (Fullscreen), `M` (Mute), `←`/`→` (Seek 10s), `Esc` (Close dialogs).
- **Toast Notifications**: Built-in JavaScript toast notification system triggered on HTMX watchlist and progress events.

---

## 4. Key Conventions & Privacy Architecture

1. **Database Privacy & `.env` Isolation**:
   - `db.sqlite3` and `.env` are strictly ignored in [`.gitignore`](file:///D:/Om/Projects/Filvora/.gitignore).
   - Local watch history, users, and passwords are never tracked or committed to GitHub.
   - When a user clones the repository, Django creates a fresh, empty local database upon running `python manage.py migrate`.
   - Environment variables must be copied from [`.env.example`](file:///D:/Om/Projects/Filvora/.env.example) to `.env`.
2. **Play Icon SVGs**:
   - **DO NOT** use Heroicons `play-circle` paths (`M10 18a8 8 0...`) inside round buttons because it creates a double-circle / target distortion.
   - **ALWAYS** use the clean solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-black translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
3. **HTMX Click Event Propagation on Cards**:
   - Cards are wrapped in clickable anchor tags.
   - Any nested action buttons (Watchlist, Remove, More Info) must include:
     `onclick="event.preventDefault(); event.stopPropagation();"`
     to prevent triggering parent link navigation.
4. **HTMX CSRF Header**:
   - `templates/base.html` configures global CSRF tokens for all HTMX requests:
     ```javascript
     document.addEventListener('htmx:configRequest', (event) => {
         event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
     });
     ```
5. **Video Player History Management**:
   - When changing servers in `templates/playback/watch.html`, use `window.location.replace('?server=' + this.value)` instead of `window.location.href = ...` so that clicking the browser "Back" button returns the user directly to the movie details page rather than looping through server selections.

---

## 5. Route Map Reference

| Route | View Function | App | Template / Type |
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
| `/progress/save/` | `save_progress` | `apps.watch` | JSON Response (Beacon) |
| `/progress/remove/` | `remove_progress` | `apps.watch` | HTMX Fragment / JSON |
| `/accounts/login/` | `login_view` | `apps.accounts` | `templates/accounts/login.html` |
| `/accounts/register/` | `register_view` | `apps.accounts` | `templates/accounts/register.html` |
| `/accounts/logout/` | `logout_view` | `apps.accounts` | Redirect to `/` |

---

## 6. Full Video Download Engine Specification (Future Implementation)

### 6.1 Background & Technical Architecture
Streaming embed servers (e.g., `Vidsrc`, `SuperEmbed`, `2Embed`) deliver video via chunked HTTP Live Streaming (HLS `.m3u8` playlists) containing hundreds of small `.ts` chunks (2–6 seconds each), encrypted with short-lived tokens and referer restrictions. Direct MP4 downloads are not directly exposed by third-party embed hosts.

### 6.2 Recommended Technical Architecture (When Ready to Build):

```text
[User Clicks Download]
        │
        ▼
[Django Background Worker / Celery / Subprocess Task]
        │
        ├── 1. Extract Master .m3u8 Stream via Scraper / Headless Parser
        ├── 2. Sequential Chunk Downloader (Pool of .ts segments to temp storage)
        ├── 3. FFmpeg Video Stitcher (`ffmpeg -i input.m3u8 -c copy output.mp4`)
        └── 4. Generate Single-Use Signed Download URL (`/download/file/<token>/`)
        │
        ▼
[User Browser Downloads Full .mp4] ──> [Auto-Cleanup Cron Deletes Temp File After 2 Hours]
```

### 6.3 Key Considerations & Resource Planning:
1. **Server Storage**: A 1080p movie is ~1.5 GB to 4 GB. Concurrent downloads require a dedicated scratch directory (e.g. `media/downloads/temp/`) with automated cron cleanup to purge completed downloads.
2. **CPU & Processing Time**: Remuxing via `ffmpeg -c copy` (stream copy) is fast (15–45 seconds) because it does not re-encode video; however, downloading 1,000 `.ts` chunks across network limits takes 1–4 minutes per movie.
3. **Scraper Resilience**: Embed providers frequently update captcha, AES decryption keys, and Cloudflare challenges. The extraction layer should be modular (`apps/playback/extractors/`) with fallback to browser-side extensions or client-side blob downloaders.

---

## 7. How to Continue Development & Next Tasks

When picking up the next development session, consider these prioritized feature enhancements:

1. **Video Download Feature Implementation**:
   - Implement the modular HLS extractor + `ffmpeg` remuxing pipeline documented in Section 6.
2. **Genre Explorer & Filter View**:
   - Add a dedicated `/genres/` or filter dropdown on `/movies/` and `/series/` to filter by TMDB Genre ID, release year, and minimum rating.
3. **User Profiles System**:
   - Allow users to create multiple profiles (e.g. "Main", "Kids", "Guest") under a single account, each maintaining independent watchlists and continue-watching history.
4. **Custom Playlists & Collections**:
   - Expand `apps.library` to support custom user-created lists (e.g. "Weekend Sci-Fi Marathon", "Oscar Winners").
5. **Enhanced Video.js Direct HLS Extraction**:
   - Add support for subtitle track (`.vtt`) auto-loading and audio track switching when direct streams are available.
6. **Automated Unit & Integration Tests**:
   - Add test suites in `apps/*/tests.py` covering TMDB mock responses, HTMX library toggle endpoints, and watch progress beacons.

---

## 8. Useful Command Shortcuts for Agents

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
