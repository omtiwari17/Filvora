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
  - All routes (`/`, `/movies/`, `/series/`, `/discover/`, `/genres/`, `/history/`, `/analytics/`, `/downloads/`, `/library/`, `/search/`) return `200 OK`.
- **Automated Test Suite**: 55 tests across all 8 apps (`apps.core`, `apps.catalog`, `apps.playback`, `apps.library`, `apps.watch`, `apps.tmdb`, `apps.accounts`, `apps.downloads`), 100% passing.

---

## 2. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, recommendation engine, backup command
│   ├── catalog/               # Browse, discover, mood explorer, genres, person profiles
│   ├── playback/              # Video player view, provider registry, server switcher
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
│   ├── css/main.css           # Glassmorphism, animations, rail scroll styles
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
    ├── 404.html               # Custom cinematic 404 error page
    └── 500.html               # Custom cinematic 500 error page
```

---

## 3. Subsystem Implementation Overview

### 3.1 Metadata & Age Ratings Engine (`apps/tmdb/client.py`)
- **TMDB API Client**: Encapsulates endpoints with dual-mode execution (Windows Schannel `curl.exe` with `--ssl-no-revoke` and `requests` fallback) and in-memory TTL caching.
- **Content Certification & Age Ratings**:
  - Movies: Queries TMDB `release_dates` (`append_to_response=release_dates`) to extract film certifications (`PG-13`, `R`, `PG`, `G`, `NC-17`, `18+`).
  - TV Series: Queries TMDB `content_ratings` (`append_to_response=content_ratings`) to extract TV ratings (`TV-MA`, `TV-14`, `TV-PG`, `TV-G`, `TV-Y7`).
  - Search & List Heuristics: Automatic genre fallback (`_attach_age_rating`).

### 3.2 Recommendation Engine (`apps/core/recommendations.py`)
- **Deterministic Affinity Scoring**: Calculates genre preference weights from completed watch history (weight 3.0), in-progress watches (weight 1.0), and saved watchlist items (weight 2.0).
- **Personalized Rails**: Injects *"Recommended For You"* and explainable *"Because You Watched [Title]"* rails on the homepage.

### 3.3 Standalone Video Download Subsystem (`apps/downloads/`)
- **DownloadJob Model**: Tracks user downloads with statuses: `QUEUED`, `DOWNLOADING`, `PROCESSING`, `READY`, `FAILED`, `CANCELLED`.
- **Deterministic Filename Service** (`apps/downloads/services/filename.py`):
  - Movies: `Movie Name (Year) [Quality].mp4` (e.g. `Interstellar (2014) [1080p].mp4`)
  - Episodes: `Series Name S01E01 [Quality].mp4` (e.g. `Breaking Bad S02E03 [720p].mp4`)
- **Background Pipeline**: Streams chunks to `media/downloads/temp/` and serves via `FileResponse` as standalone attachment.

### 3.4 User Profiles & Kids Safety Mode (`apps/accounts/`)
- **UserProfile Model**: Supports multiple user profiles with custom avatars and `is_kids` boolean flag.
- **Session Profile Switching**: Active profile stored in `request.session['active_profile_id']`.
- **Server-Side Content Filtering**: Gated discovery and detail views enforce `certification.lte=PG` for kids profiles.

### 3.5 Personal Analytics & Filvora Wrapped (`apps/watch/`)
- **Metrics**: Computes total watch hours, movie and episode counts, completed titles, and genre affinity breakdown.
- **Filvora Wrapped 2026**: Interactive celebratory showcase celebrating user milestones and favorite genres.

### 3.6 PWA & Mobile Shell (`static/`)
- **Web App Manifest**: `static/manifest.json` configured for standalone display.
- **Service Worker**: `static/sw.js` caches shell assets (`main.css`, `main.js`) with network-first for dynamic content.

---

## 4. Key Conventions & Rules

1. **Database Privacy & `.env` Isolation**:
   - `db.sqlite3`, `backups/`, `media/`, and `.env` are strictly ignored in `.gitignore`.
2. **Play Icon SVGs**:
   - Never use double-circle `play-circle` inside circular buttons. Always use solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-white translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
3. **HTMX Event Propagation**:
   - Nested action buttons inside clickable cards must include `onclick="event.preventDefault(); event.stopPropagation();"`.

---

## 5. Useful Commands

```powershell
# Run Development Server
.\venv\Scripts\python.exe manage.py runserver

# Run Automated Test Suite (55 tests)
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts apps.downloads

# Backup Local Database
.\venv\Scripts\python.exe manage.py backup_db
```
