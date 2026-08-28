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
  - Django Development Server is active on **`http://127.0.0.1:8000/`** & **`http://192.168.1.5:8000/`**
  - Command: `.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000`
  - All routes (`/`, `/movies/`, `/series/`, `/discover/`, `/genres/`, `/history/`, `/analytics/`, `/downloads/`, `/library/`, `/search/`, `/watch/`) return `200 OK`.
- **Automated Test Suite**: **89 tests** across all 8 apps (`apps.core`, `apps.catalog`, `apps.playback`, `apps.library`, `apps.watch`, `apps.tmdb`, `apps.accounts`, `apps.downloads`), 100% passing.

---

## 2. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, recommendation engine, backup command
│   ├── catalog/               # Browse, discover, mood explorer, genres, person profiles
│   ├── playback/              # Video player view, provider registry, server switcher, diagnostics
│   ├── watch/                 # Watch progress beacon, watch history, analytics & Wrapped
│   ├── library/               # Watchlist, custom collections & playlists
│   ├── downloads/             # Standalone download pipeline, DownloadJob model & dashboard
│   ├── tmdb/                  # TMDB API client with curl/requests fallback & caching
│   └── accounts/              # Authentication & UserProfile multi-profile switcher
├── config/
│   ├── settings.py            # Hardened Django settings & remote proxy configurations
│   ├── urls.py                # Main URL routing definitions
│   └── wsgi.py / asgi.py      # WSGI/ASGI application gateways
├── deploy/
│   ├── Caddyfile              # Zero-config automatic HTTPS reverse proxy
│   ├── nginx.conf             # Hardened Nginx reverse proxy configuration
│   ├── Dockerfile             # Production container definition
│   ├── docker-compose.yml     # Multi-container web + proxy stack
│   └── README.md              # Remote access & Tailscale/Cloudflare guide
├── static/
│   ├── css/main.css           # Glassmorphism, animations, scrollbar-hide styles
│   ├── js/main.js             # Rail drag-scroll, keyboard shortcuts, toast engine
│   ├── manifest.json          # PWA Web App Manifest
│   └── sw.js                  # PWA Service Worker caching
└── templates/
    ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav
    ├── components/            # Reusable partials (movie_card, series_card, empty_state)
    ├── catalog/               # Browse, discover, genres, and person detail views
    ├── watch/                 # History and Personal Analytics (Wrapped) templates
    ├── downloads/             # Live polling download dashboard & partials
    ├── library/               # Watchlist and custom collections manager
    ├── accounts/              # Sign in, registration, and profile switcher
    ├── playback/              # Immersive cinematic player view with server switcher
    ├── 404.html               # Custom cinematic 404 error page
    └── 500.html               # Custom cinematic 500 error page
```

---

## 3. Subsystem Implementation Overview

### 3.1 Metadata & Dynamic Age Ratings Engine (`apps/tmdb/client.py`)
- **TMDB API Client**: Encapsulates endpoints with dual-mode execution (Windows Schannel `curl.exe` with `--ssl-no-revoke` and `requests` fallback) and in-memory TTL caching.
- **Dynamic Content Certification & Singleton Rating Cache (`_RATING_CACHE`)**:
  - Automatically queries official TMDB release certifications (`/movie/{id}/release_dates` and `/tv/{id}/content_ratings`) when rating is not bundled in list responses.
  - Ensures 100% rating consistency between listing cards and detail pages (e.g. *Call Me by Your Name* consistently displays `R`).
  - Caches extracted ratings in `_RATING_CACHE[media_type:tmdb_id]` across all app requests.

### 3.2 Balanced Responsive Grid Engine (`apps/tmdb/client.py`)
- **24-Item Page Windowing (`_fetch_paginated_24`)**:
  - TMDB API returns 20 items per page by default, which causes awkward orphan cards in 6-column desktop grids ($20 \pmod 6 = 2$).
  - `_fetch_paginated_24` concatenates across TMDB page boundaries and slices exactly **24 titles per page**.
  - Creates 100% full, even rows across every device breakpoint:
    - 🖥️ **Desktop (6 columns)**: Exactly **4 complete rows** of 6.
    - 💻 **Medium (4 columns)**: Exactly **6 complete rows** of 4.
    - 📱 **Tablet (3 columns)**: Exactly **8 complete rows** of 3.
    - 📲 **Mobile (2 columns)**: Exactly **12 complete rows** of 2.

### 3.3 Multi-Page Discover Engine (`apps/catalog/views.py`, `templates/catalog/discover.html`)
- **Faceted Search & Pagination**:
  - Supports combinations of **Media Type** (`movie`/`tv`), **Mood**, **Genre**, **Language**, **Rating / Score**, **Certification**, and **Sort Order**.
  - Full pagination controls (`← Previous`, page numbers, `Next →`) with complete query parameter preservation across page transitions.

### 3.4 Advanced Playback Subsystem (`apps/playback/`, `templates/playback/watch.html`)
- **Fullscreen Controls Preservation**:
  - In native Full Screen mode (via <kbd>F</kbd> key, Video.js button, or top bar Fullscreen button), `#top-sensor`, `#quick-server-container`, `#player-overlay`, and modals are mounted directly inside `player.el()` with `z-index: 2147483647` so they remain interactive in native browser fullscreen.
- **Direct Hover Server Switcher**:
  - Floating top-right pill (`Server VIDLINK ⌵`) expands a glassmorphic server dropdown instantly upon cursor hover.
- **Playback-Driven Progress & Resume Threshold**:
  - Removed blind background timers. Watch progress is only recorded when media is actively playing (`!player.paused()` and `currentTime >= 15s`).
  - Resume prompts strictly require $\ge 30$ seconds of verified watch time.
- **Auto-Hide Controls on Pause**:
  - Player controls, big play button, and top navigation auto-hide after 3.5 seconds of inactivity even when paused.

### 3.5 Season-Wise Playtime Breakdown & Analytics (`apps/watch/views.py`, `templates/watch/analytics.html`)
- **Season Playtime Aggregation**:
  - Aggregates user watch history by series and season to compute total watch hours per season (`Season 1: 5.4 hrs`).
  - Displays playtime badges on TV series season tabs and a dedicated breakdown table in Personal Analytics (`/analytics/`).

### 3.6 UI Polish & Scrollbar Suppression (`static/css/main.css`)
- Replaced emoji icons with clean, scalable Tailwind SVG icons.
- Suppressed native browser horizontal scrollbars on carousels, genre pills, mood tabs, and cast rails across Chrome, Safari, Firefox, and Edge.

### 3.7 Standalone Video Download Subsystem (`apps/downloads/`)
- **DownloadJob Model**: Tracks user downloads with UUID PK and statuses: `QUEUED`, `DOWNLOADING`, `PROCESSING`, `READY`, `FAILED`, `CANCELLED`.
- **Provider Abstraction Layer** (`apps/downloads/providers/`):
  - `base.py`: Defines `DownloadProvider` abstract interface separating playback capability from authorized download capability.
  - `registry.py`: Provider registry with priority resolution and dynamic available quality querying.
- **Deterministic Filename Service** (`apps/downloads/services/filename.py`):
  - Movies: `Movie Name (Year) [Quality].mp4` (e.g. `Interstellar (2014) [1080p].mp4`)
  - Episodes: `Series Name S01E01 [Quality].mp4` (e.g. `Breaking Bad S02E03 [720p].mp4`, strictly omitting episode title).
  - Sanitization of all Windows-illegal filesystem characters (`\/*?:"<>|`).
- **Complete Pipeline Services** (`apps/downloads/services/`):
  - `storage.py`: Per-job temporary directory isolation (`media/downloads/temp/job_<id>/{source,processing,output}`), disk space pre-flight estimation checks, and human-readable size formatting.
  - `downloader.py`: Dual-mode download engine (Windows Schannel `curl.exe` with `--ssl-no-revoke` and `requests` fallback with streaming chunks).
  - `processor.py`: FFmpeg processing engine preferring fast, zero-quality-loss remuxing (stream copy) with H.264/AAC re-encoding fallback.
  - `validator.py`: Strict post-processing validation verifying file existence, non-zero size, container readability, and video/audio stream integrity (via `ffprobe` or file inspection).
  - `cleanup.py`: Immediate per-job temp data removal, orphan directory cleanup for crash/power loss recovery, and age-based eviction.
  - `manager.py`: Complete lifecycle orchestrator handling job creation, worker dispatch, state transitions, retry of failed/cancelled jobs, and concurrency safety.
- **Celery-Ready Background Tasks** (`apps/downloads/tasks.py`):
  - Thread-based background workers structured with a clean Celery-compatible interface.
- **Standby & UI Gating**:
  - The complete backend pipeline, models, services, providers, views, and test suite remain 100% intact in `apps/downloads/`.
  - User-facing download buttons on movie/series detail pages and navbar are hidden from the UI since 3rd-party iframe playback providers (VidLink, AutoEmbed, 2Embed, NontonGo, VidSrc) do not offer direct MP4 download links. The subsystem is ready for immediate activation whenever direct download mirrors or authorized storage backends are added in the future.

### 3.8 User Profiles & Kids Safety Mode (`apps/accounts/`)
- **UserProfile Model**: Supports multiple user profiles with custom avatars and `is_kids` boolean flag.
- **Session Profile Switching**: Active profile stored in `request.session['active_profile_id']`.
- **Server-Side Content Filtering**: Gated discovery and detail views enforce `certification.lte=PG` for kids profiles.

---

## 4. Key Conventions & Rules

1. **Database Privacy & `.env` Isolation**:
   - `db.sqlite3`, `backups/`, `media/`, and `.env` are strictly ignored in `.gitignore`.
2. **Git Commit & Push**:
   - Always stage, commit with clear semantic messages, and `git push origin main` after completing tasks.
   - Do NOT commit the `FILVORA_PHASED_WORK_GUIDE` folder.
3. **Play Icon SVGs**:
   - Never use double-circle `play-circle` inside circular buttons. Always use solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-white translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
4. **HTMX Event Propagation**:
   - Nested action buttons inside clickable cards must include `onclick="event.preventDefault(); event.stopPropagation();"`.

---

## 5. Useful Commands & Credentials Reference

```powershell
# Run Development Server (accessible locally and on LAN)
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# Run Automated Test Suite (89 tests across 8 apps)
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts apps.downloads

# Backup Local Database
.\venv\Scripts\python.exe manage.py backup_db

# Reset / Change User Password
.\venv\Scripts\python.exe manage.py changepassword moon
```

### Local Test Accounts:
- **Main User**: `moon` (Password: `1234`)
- **Superuser**: `admin` (Password: `1234`)
