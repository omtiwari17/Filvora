# 🤖 AGENTS.MD — Filvora Engineering Master Specification & Session Continuation Guide

> **Purpose of this Document**:  
> This file is the primary context and handover document for any AI agent or software engineer continuing work on the **Filvora** codebase. It documents the exact current state of the application, architecture, conventions, active background processes, database models, frontend interaction patterns, known quirks, what works vs. what is not active, and upcoming roadmap items.

---

## 1. System Environment & Runtime State

### 1.1 Local Environment
- **Operating System**: Windows (PowerShell)
- **Project Root**: `D:\Om\Projects\Filvora`
- **Python Virtualenv**: `D:\Om\Projects\Filvora\venv`
  - Python Executable: `.\venv\Scripts\python.exe`
- **Django Version**: 5.2+ (Django REST Framework, Requests, Python-Dotenv, curl-cffi, pynacl)
- **Active Server Task**: 
  - Django Development Server is active on **`http://127.0.0.1:8000/`** & **`http://192.168.1.5:8000/`**
  - Command: `.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000`
  - All active routes (`/`, `/movies/`, `/series/`, `/discover/`, `/genres/`, `/history/`, `/analytics/`, `/library/`, `/search/`, `/watch/`) return `200 OK`.
- **One-Click Launcher**:
  - `Start Filvora.bat` located at root: verifies venv, silently checks database migrations, auto-opens browser, and runs dev server bound to `0.0.0.0:8000`.
- **Automated Test Suite**: **97 tests** across all 8 apps (`apps.core`, `apps.catalog`, `apps.playback`, `apps.library`, `apps.watch`, `apps.tmdb`, `apps.accounts`, `apps.downloads`), **100% passing**.

---

## 2. Feature Status: What Works vs. What Is On Standby / Inactive

### 2.1 ✅ Active & 100% Working Features

| **Multi-Profile Isolation Engine (History, Ratings & Analytics)** | `apps/accounts/`, `apps/watch/`, `apps/catalog/`, `apps/playback/` | Full multi-profile isolation with session-aware active profile switching. Each profile ([`UserProfile`](file:///D:/Om/Projects/Filvora/apps/accounts/models.py#L6)) maintains its own completely independent watch history timeline rails, continue watching list, rating scores (1–5 stars), resume timestamps, and personal analytics / Wrapped metrics. Profiles include custom avatars and `is_kids` boolean flag enforcing server-side `certification.lte=PG` content filtering. |
| **Interactive User Ratings & Affinity Engine** | `apps/watch/`, `apps/core/`, `templates/components/` | Custom `UserRating` model (1–5 stars, unique per user profile/media). Interactive HTMX star rating widget with instant left-to-right JavaScript cascade hover animations (hovering star $N$ lights up stars $1 \dots N$ gold with `scale(1.2)`). Users can rate already-watched OR unstreamed titles directly from Movie/Series detail pages (`/movies/<id>/`, `/series/<id>/`), Watchlist (`/library/`), and Watch History (`/history/`). Powers `RecommendationEngine` by weighting 4–5 star titles (+5 affinity), 3 star titles (+2 affinity), and 1–2 star titles (-2 penalty) and driving "Because You Watched / Loved" suggestions per active profile. |
| **Multi-Tab Watch History & Rated Hub** | `apps/watch/`, `templates/watch/history.html` | Dual-tab history dashboard scoped per active profile featuring: (1) **Streamed History** with grouped timeline rails (*Today, Yesterday, This Week, Earlier*), progress bars, and single-item removal, and (2) **Rated Titles** tab displaying a dedicated poster grid of all user-rated content with live star badges and in-place rating adjustments. |
| **Multi-Server Online Playback** | `apps/playback/` | Full multi-server web player with 6 streaming providers: **VidLink** (Primary Fast 1080p HD, Default), **VidFast** (4K Ultra HD), **AutoEmbed**, **VidSrc** (UHD/HD active mirror `vidsrc.pm`), **2Embed**, **NontonGo**. Fullscreen overlay preservation, direct hover server switcher dropdown, wildcard origin iframe permissions (`allow="fullscreen *; ..."` allowing embedded player internal fullscreen), universal `document.documentElement` fullscreen toggle button, resume prompt threshold ($\ge 30$s scoped per active profile), active beacon progress tracking ($\ge 15$s), 3.5s pause auto-hide. |
| **Season Total Runtime & Analytics Engine** | `apps/catalog/`, `apps/watch/` | Aggregates individual episode runtimes per TV season via `format_season_runtime` in `apps/catalog/views.py`. Displays duration badges directly on season selector tabs (`Season 1 • 6h 38m`) and episode list meta headers (`Season 1 • 8 Episodes • 6h 38m Total`). Aggregates user watch history by season badges (`Season 1: 5.4 hrs`) in Personal Analytics & Filvora Wrapped (`/analytics/`), with 5-metric dashboard including **Avg Rating** and total rated counts for the active profile. |
| **Dynamic Age Ratings Engine** | `apps/tmdb/client.py` | Automatically extracts official release certifications (`PG`, `PG-13`, `R`, `TV-MA`) from TMDB and caches them in singleton `_RATING_CACHE[media_type:tmdb_id]` across all views. Ensures 100% rating consistency between cards and detail pages. |
| **Balanced Responsive Grid Engine** | `apps/tmdb/client.py` | `_fetch_paginated_24` windowing creates perfectly full, even rows of 24 titles per page (Desktop: 4 rows of 6; Laptop: 6 rows of 4; Tablet: 8 rows of 3; Mobile: 12 rows of 2). |
| **Multi-Page Discover Engine** | `apps/catalog/` | Faceted multi-page discovery filtering by Media Type (`movie`/`tv`), Mood, Genre, Language, Score, Certification (`G`, `PG`, `PG-13`, `R`, `NC-17`), and Sort Order with preserved query parameters across pagination. |
| **Library & Collections** | `apps/library/` | One-click Watchlist toggling via HTMX, custom user collections, playlist management, and inline star rating controls. |
| **Homepage Cinematic Billboard** | `templates/home/index.html` | Hero spotlight billboard with backdrop image blending, action buttons (Play Now, In My List, Details), and responsive spacing avoiding overlap with the "Continue Watching" rail. |
| **Mobile-First UX & App Navigation** | `templates/base.html`, `static/css/main.css` | Native app-like mobile experience with iOS/Android safe area insets (`env(safe-area-inset-bottom)`), active pill bottom navigation, mobile poster rating badges (visible without hover), full-width touch CTA buttons on detail views, horizontal touch-swipe season selector rails, and search bar boundary bounds. |
| **Zero Emojis / Strict SVG Design** | `static/css/`, `static/js/`, `templates/` | 100% clean Tailwind SVGs across all components (metrics, badges, fallback posters, dropdowns, bat launcher, buttons). Suppressed native horizontal scrollbars on carousels/rails, rail drag-scroll, keyboard shortcuts (<kbd>F</kbd> for fullscreen, <kbd>Space</kbd> for play/pause, <kbd>M</kbd> for mute, <kbd>Alt</kbd>+<kbd>S</kbd> for server switch). |

---

### 2.2 📺 Playback Architecture & Embed Mechanics (`apps/playback/`)

#### Streaming Providers Matrix:
1. **Server 1 (VidLink)** ⭐: Primary fast 1080p Full HD default server with reliable CDN routing and zero buffer stalls.
2. **Server 2 (VidFast)**: High-bitrate 4K Ultra HD & 1080p streaming node. Runs on automatic adaptive bitrate (ABR); its internal UI exposes playback speed while serving peak source resolution.
3. **Server 3 (AutoEmbed)**: Multi-source failover streaming node.
4. **Server 4 (VidSrc)**: High-definition embed mirror (`vidsrc.pm`).
5. **Server 5 (2Embed)**: Secondary backup stream node.
6. **Server 6 (NontonGo)**: Alternative multi-server backup.

#### Fullscreen & Iframe Delegation Architecture:
- **Iframe Permissions Policy**: The player `<iframe>` uses wildcard origin permissions:
  ```html
  <iframe
      id="filvora-embed-frame"
      src="{{ video_url }}"
      allow="accelerometer *; autoplay *; clipboard-write *; encrypted-media *; gyroscope *; picture-in-picture *; web-share *; fullscreen *; display-capture *"
      allowfullscreen="true"
      webkitallowfullscreen="true"
      mozallowfullscreen="true"
      oallowfullscreen="true"
      msallowfullscreen="true"
  ></iframe>
  ```
  The `fullscreen *` wildcard is strictly required by modern Chromium/WebKit browsers so that internal video elements and nested iframes inside the embed provider have permission to trigger full screen via their own bottom-right `[ ⛶ ]` button.
- **Top-Bar Fullscreen API**: Filvora's top-right `[⛶ Fullscreen]` button executes `document.documentElement.requestFullscreen()` directly on the root HTML element, expanding both the player and top navigation controls.
- **Focus Context & Keyboard Shortcuts**:
  - Clicking inside an external iframe transfers browser keyboard focus into the cross-origin frame. Because third-party embed scripts do not intercept the <kbd>F</kbd> key, key events are not processed while the iframe retains focus.
  - Moving the mouse cursor into the top 120px sensor or hovering over the top navigation automatically invokes `window.focus()`, immediately restoring Filvora's global keyboard shortcut listeners (<kbd>F</kbd> for Fullscreen, <kbd>Alt</kbd>+<kbd>S</kbd> for server switch, <kbd>Esc</kbd> for exit).

---

### 2.3 ⚠️ Standby / Inactive Subsystem: Video Downloads (`apps/downloads/`)

> **IMPORTANT**: Standalone offline video downloading is **NOT an active user-facing feature**. All download buttons and links are hidden from the user interface.

#### Why Video Downloading is Not Active For Users:
1. **Third-Party Iframe Embed Gating**: Filvora does not self-host video files; it uses 6 third-party embed providers (VidLink, VidFast, AutoEmbed, VidSrc, 2Embed, NontonGo) for web streaming. These providers stream via tokenized, obfuscated web player iframes and explicitly block direct external MP4 downloading using Cloudflare WAF, IP rate-limits, and session tokens (`"requiresProxy": true`).
2. **Rejection of Trailers & Dummy Files**:
   - TMDB API only provides YouTube promotional trailer keys (2–3 minute clips @ ~7.5 MB), NOT full movies. Downloading trailers as movies was explicitly rejected.
   - Fake 100 KB placeholder files were also explicitly rejected.
3. **Standby Architecture Preserved**:
   - The complete, production-grade download pipeline architecture (`apps/downloads/`) remains 100% intact in the codebase:
     - `models.py`: `DownloadJob` model with UUID PK, status state machine, progress tracking, and file metadata.
     - `services/`: Filename sanitization service, isolated per-job storage (`media/downloads/temp/`), dual-mode downloader (`curl` + `requests` with chunk streaming), FFmpeg processor, validator, and orphan cleanup.
     - `providers/`: `DownloadProvider` abstract interface and registry.
     - `tests.py`: **34 comprehensive unit tests** all passing 100%.

---

## 3. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, recommendation engine (weighted with ratings), backup command
│   ├── catalog/               # Browse, discover, mood explorer, genres, person profiles, detail views with ratings
│   ├── playback/              # Video player view, provider registry, server switcher, diagnostics
│   ├── watch/                 # WatchProgress & UserRating models, history (with tabs), analytics & Wrapped
│   ├── library/               # Watchlist, custom collections & playlists with rating support
│   ├── downloads/             # Standby download pipeline, DownloadJob model, services & 34 tests
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
│   ├── css/main.css           # Glassmorphism, animations, scrollbar-hide styles, star cascade hover CSS
│   ├── js/main.js             # Rail drag-scroll, keyboard shortcuts, toast engine, star rating hover engine
│   ├── manifest.json          # PWA Web App Manifest
│   └── sw.js                  # PWA Service Worker caching
├── Start Filvora.bat          # Double-clickable launcher for Windows (venv check, migrations, browser launch)
└── templates/
    ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav
    ├── components/            # Reusable partials (movie_card, series_card, empty_state, rating_stars)
    ├── catalog/               # Browse, discover, genres, and person detail views
    ├── watch/                 # History (Streamed & Rated tabs) and Personal Analytics (Wrapped) templates
    ├── downloads/             # Standby download dashboard & dialog partials
    ├── library/               # Watchlist and custom collections manager
    ├── accounts/              # Sign in, registration, and profile switcher
    ├── playback/              # Immersive cinematic player view with server switcher
    ├── 404.html               # Custom cinematic 404 error page
    └── 500.html               # Custom cinematic 500 error page
```

---

## 4. Key Conventions & Rules

1. **Database Privacy & `.env` Isolation**:
   - `db.sqlite3`, `backups/`, `media/`, and `.env` are strictly ignored in `.gitignore`.
2. **Git Commit & Push**:
   - Always stage, commit with clear semantic messages, and `git push origin main` after completing tasks.
   - Do NOT commit the `FILVORA_PHASED_WORK_GUIDE` folder.
3. **Play Icon SVGs & No Emoji Policy**:
   - Never use double-circle `play-circle` inside circular buttons. Always use solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-white translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
   - Never use emoji characters (e.g. 🎬, 📺, ⭐, 🏆) in HTML templates, options, or scripts. Always use clean Tailwind SVG icons.
4. **HTMX Event Propagation**:
   - Nested action buttons inside clickable cards must include `onclick="event.preventDefault(); event.stopPropagation();"`.
5. **No Fake / Deceptive Content**:
   - Never download trailer clips or dummy files and label them as full movies. Keep features genuine and honest.

---

## 5. Useful Commands & Credentials Reference

```powershell
# Double-click launcher (or run in shell)
.\Start Filvora.bat

# Run Development Server manually
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# Run Automated Test Suite (97 tests across 8 apps)
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts apps.downloads

# Backup Local Database
.\venv\Scripts\python.exe manage.py backup_db

# Reset / Change User Password
.\venv\Scripts\python.exe manage.py changepassword moon
```

### Local Test Accounts:
- **Main User**: `moon` (Password: `1234`)
- **Superuser**: `admin` (Password: `1234`)
