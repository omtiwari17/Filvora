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

### 2.1 ✅ Active & 100% Working Features (v2.3 Production State)

| **Official Franchise & Saga Universe Rail** | `apps/tmdb/`, `apps/catalog/`, `templates/catalog/movie_detail.html` | Auto-detects if a movie belongs to an official TMDB collection/franchise (e.g. *Dune, Harry Potter, Spider-Man, John Wick, Avatar, Marvel*). Fetches all installments chronologically ordered by release date, displays saga overview and total film count, assigns chronological order badges (`#1`, `#2`, `#3`...), highlights the currently viewed film with a glowing border and `Now Viewing` indicator, and provides instant play/details actions. |
| **Official Cinematic 4K/HD Trailer Modal** | `apps/tmdb/`, `apps/catalog/`, `templates/components/trailer_modal.html` | Watch official trailers on movie detail, series detail, and homepage hero billboard without leaving the page. Built with privacy-focused YouTube embeds (`youtube-nocookie`), autoplay, zero-emoji SVG controls, instant audio/playback cutoff on dismiss, keyboard escape dismissal, and dynamic `/trailer/<media_type>/<tmdb_id>/` on-demand API fallback. |
| **Director, Creator & Interactive Cast Showcase** | `apps/catalog/`, `templates/catalog/` | Extracted official directors with dedicated badges on movie detail views, showrunners/creators on TV series detail views, and interactive clickable avatar cards linking straight to the artist's full filmography page (`/person/<id>/`) supporting both crew and cast credits. |
| **Smart TV Episode Autoplay & Up Next Overlay** | `apps/playback/`, `templates/playback/` | Intelligent episodic advance engine with season boundary rollover (smoothly transitioning from e.g. S1E8 to S2E1). Bottom-right cinematic modal with episode still thumbnail, episode title, season/episode tags, animated 8-second countdown progress bar, and instant "Play Now" action. Triggered on Video.js `ended` event and embed `postMessage` triggers ($\ge 95\%$ or $\le 25$s remaining). |
| **Profile Management Hub & Custom Avatar Themes** | `apps/accounts/`, `templates/accounts/` | Edit profile name, toggle Kids mode with animated glassmorphic iOS-style toggle switches, and select custom avatar color themes (🔴 Crimson, 🔵 Sapphire, 🟢 Emerald, 🟣 Purple, 🟡 Amber). |
| **Wi-Fi LAN Streaming & Mobile/TV QR Code Pairing** | `apps/accounts/`, `templates/accounts/`, `templates/includes/` | Dynamic local IP resolver (`get_local_ip`) displaying LAN access link (`http://192.168.1.x:8000`) in user dropdown and profile switcher. Features a 1-click **Scan to Watch** QR Code modal for instant mobile camera / Smart TV pairing without typing IP addresses. |
| **Quick Vibe & Mood Randomizer in Navbar** | `templates/includes/navbar.html`, `apps/catalog/`, `static/js/main.js`, `static/css/main.css` | Dual-mode responsive ambient discovery dropdown offering instant mood leaps (*Adrenaline Rush, Mind-Bending, Laugh Out Loud, Relax & Chill, Surprise Me*) powered by `/surprise-me/` backend engine. Features strict zero-emoji Tailwind SVG design, `@media (hover: hover) and (pointer: fine)` hover decoupling, and state-based tap-to-open / tap-to-close toggle and click-outside dismissal eliminating sticky mobile hover issues. |
| **Enhanced Watchlist / Library Filter & Sort Engine** | `templates/library/list.html`, `apps/library/` | Live client-side search input, Type selector (All / Movies / Series), Star Rating filters (All / Any Rated / 5 Stars / 4+ Stars / 3+ Stars / Unrated), multi-criteria sorting (Recently Added, Title A-Z, Title Z-A, TMDB Score, My Rating), live item count badge, and clean no-match empty state. |
| **Multi-Profile Isolation Engine (History, Ratings, Watchlist, Collections & Server Preferences)** | `apps/accounts/`, `apps/watch/`, `apps/catalog/`, `apps/playback/`, `apps/library/` | Full multi-profile isolation with session-aware active profile switching. Each profile ([`UserProfile`](file:///D:/Om/Projects/Filvora/apps/accounts/models.py#L6)) maintains its own completely independent watch history timeline rails, continue watching list, Watchlist ("My List"), custom playlists/collections, server preferences, rating scores (1–5 stars), resume timestamps, and personal analytics / Wrapped metrics. Enforces server-side `certification.lte=PG` content filtering for Kids profiles. |
| **Interactive User Ratings & Affinity Engine** | `apps/watch/`, `apps/core/`, `templates/components/` | Custom `UserRating` model (1–5 stars, unique per user profile/media). Interactive HTMX star rating widget with instant left-to-right JavaScript cascade hover animations. Weighting 4–5 star titles (+5 affinity), 3 star titles (+2 affinity), and 1–2 star titles (-2 penalty) driving "Because You Watched / Loved" suggestions per active profile. |
| **Multi-Tab Watch History & Rated Hub** | `apps/watch/`, `templates/watch/history.html` | Dual-tab history dashboard scoped per active profile featuring: (1) **Streamed History** with grouped timeline rails (*Today, Yesterday, This Week, Earlier*), progress bars, and single-item removal, and (2) **Rated Titles** tab displaying a dedicated poster grid of all user-rated content with live star badges and in-place rating adjustments. |
| **Multi-Server Online Playback** | `apps/playback/` | Full multi-server web player with 6 streaming providers: **VidLink** (Primary Fast 1080p HD, Default), **VidFast** (4K Ultra HD), **AutoEmbed**, **VidSrc** (UHD/HD active mirror `vidsrc.pm`), **2Embed**, **NontonGo**. Fullscreen overlay preservation, direct hover server switcher dropdown, profile-isolated server preference memory, wildcard origin iframe permissions, universal fullscreen toggle button, resume prompt threshold ($\ge 30$s scoped per active profile), active beacon progress tracking ($\ge 15$s), 3.5s pause auto-hide. |
| **Season Total Runtime & Analytics Engine** | `apps/catalog/`, `apps/watch/` | Aggregates individual episode runtimes per TV season via `format_season_runtime` in `apps/catalog/views.py`. Displays duration badges on season selector tabs (`Season 1 • 6h 38m`) and episode list meta headers. Aggregates user watch history by season badges in Personal Analytics & Filvora Wrapped (`/analytics/`), with 5-metric dashboard including **Avg Rating** and total rated counts for active profile. |
| **Dynamic Age Ratings Engine** | `apps/tmdb/client.py` | Automatically extracts official release certifications (`PG`, `PG-13`, `R`, `TV-MA`) from TMDB and caches them in singleton `_RATING_CACHE[media_type:tmdb_id]` across all views. Ensures 100% rating consistency between cards and detail pages. |
| **Balanced Responsive Grid Engine** | `apps/tmdb/client.py` | `_fetch_paginated_24` windowing creates perfectly full, even rows of 24 titles per page (Desktop: 4 rows of 6; Laptop: 6 rows of 4; Tablet: 8 rows of 3; Mobile: 12 rows of 2). |
| **Multi-Page Discover Engine** | `apps/catalog/` | Faceted multi-page discovery filtering by Media Type (`movie`/`tv`), Mood, Genre, Language, Score, Certification (`G`, `PG`, `PG-13`, `R`, `NC-17`), and Sort Order with preserved query parameters across pagination. |
| **Homepage Cinematic Billboard** | `templates/home/index.html` | Hero spotlight billboard with backdrop image blending, action buttons (Play Now, In My List, Details), and responsive spacing avoiding overlap with the "Continue Watching" rail. |
| **Mobile-First UX & App Navigation** | `templates/base.html`, `static/css/main.css` | Native app-like mobile experience with iOS/Android safe area insets (`env(safe-area-inset-bottom)`), active pill bottom navigation, mobile poster rating badges, full-width touch CTA buttons on detail views, horizontal touch-swipe season selector rails, and search bar boundary bounds. |
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

---

## 3. Project Architecture & Apps Overview

```text
Filvora/
├── apps/
│   ├── core/                  # Homepage views, recommendation engine (weighted with ratings), backup command
│   ├── catalog/               # Browse, discover, mood explorer, genres, person profiles, detail views with ratings
│   ├── playback/              # Video player view, provider registry, server switcher, diagnostics, smart autoplay
│   ├── watch/                 # WatchProgress & UserRating models, history (with tabs), analytics & Wrapped
│   ├── library/               # Watchlist (with live search & star filters), custom collections & playlists
│   ├── downloads/             # Standby download pipeline, DownloadJob model, services & 34 tests
│   ├── tmdb/                  # TMDB API client with curl/requests fallback & caching
│   └── accounts/              # Authentication, UserProfile multi-profile switcher & QR pairing
├── config/
│   ├── settings.py            # Hardened Django settings & remote proxy configurations
│   ├── urls.py                # Main URL routing definitions
│   └── wsgi.py / asgi.py      # WSGI/ASGI application gateways
├── static/
│   ├── css/main.css           # Glassmorphism, animations, scrollbar-hide styles, star cascade hover CSS
│   ├── js/main.js             # Rail drag-scroll, keyboard shortcuts, toast engine, star rating hover engine (v2.3)
│   ├── manifest.json          # PWA Web App Manifest
│   └── sw.js                  # PWA Service Worker caching
├── Start Filvora.bat          # Double-clickable launcher for Windows (venv check, migrations, browser launch)
└── templates/
    ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav (v2.3)
    ├── components/            # Reusable partials (movie_card, series_card, empty_state, rating_stars)
    ├── catalog/               # Browse, discover, genres, and person detail views
    ├── watch/                 # History (Streamed & Rated tabs) and Personal Analytics (Wrapped) templates
    ├── library/               # Watchlist (live search & star filters) and custom collections manager
    ├── accounts/              # Sign in, registration (v2.3), profile switcher with QR code pairing & edit modals
    ├── playback/              # Immersive cinematic player view with Up Next autoplay overlay (v2.3)
    ├── 404.html               # Custom cinematic 404 error page
    └── 500.html               # Custom cinematic 500 error page
```

---

## 4. Key Conventions & Rules

1. **Universal Version Bump Synchronization (MANDATORY)**:
   - When bumping the application version (e.g., from `v2.2` to `v2.3`), you **MUST update all version occurrences simultaneously across the entire project**:
     - `templates/base.html`: `<title>` tag, footer logo badge, and footer release span (`v2.3.0-release`).
     - `templates/includes/navbar.html`: Logo badge next to FILVORA brand title.
     - `templates/playback/watch.html`: Player header badge next to video title.
     - `templates/accounts/login.html`: Header badge and page `<title>`.
     - `templates/accounts/register.html`: Header badge and page `<title>`.
     - `static/js/main.js`: File header docstring and Shortcuts modal title badge (`v2.3`).
     - `README.md`: Header and introductory overview description.
     - `AGENTS.md`: Version specifications and architecture state.
2. **Database Privacy & `.env` Isolation**:
   - `db.sqlite3`, `backups/`, `media/`, and `.env` are strictly ignored in `.gitignore`.
3. **Git Commit & Push**:
   - Always stage, commit with clear semantic messages, and `git push origin main` after completing tasks.
   - Do NOT commit the `FILVORA_PHASED_WORK_GUIDE` folder.
4. **Play Icon SVGs & Strict Zero-Emoji Policy**:
   - Never use double-circle `play-circle` inside circular buttons. Always use solid geometric play triangle:
     ```html
     <svg class="w-4 h-4 fill-white translate-x-0.5" viewBox="0 0 24 24">
         <path d="M8 5v14l11-7z"/>
     </svg>
     ```
   - Never use unicode emoji characters (e.g. 🎬, 📺, ⭐, 🏆, ⚡, 🌀, 😂, ☕, 🎲) in HTML templates, options, or scripts. Always use clean Tailwind SVG icons.
5. **HTMX Event Propagation**:
   - Nested action buttons inside clickable cards must include `onclick="event.preventDefault(); event.stopPropagation();"`.
6. **No Fake / Deceptive Content**:
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
