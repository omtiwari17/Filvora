# 🎬 Filvora v2.2 — Next-Gen Cinema & Series Streaming Engine

[![Django](https://img.shields.io/badge/Django-5.2+-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38bdf8?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![HTMX](https://img.shields.io/badge/HTMX-1.9+-3366cc?style=for-the-badge&logo=htmx&logoColor=white)](https://htmx.org/)
[![TMDB API](https://img.shields.io/badge/TMDB-API_v3-01d277?style=for-the-badge&logo=themoviedatabase&logoColor=white)](https://www.themoviedb.org/)
[![Video.js](https://img.shields.io/badge/Video.js-Player-ff0000?style=for-the-badge&logo=video.js&logoColor=white)](https://videojs.com/)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-purple?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)

**Filvora v2.2** is a complete, production-grade cinematic movie and TV series streaming application. Built on **Django 5.2**, **Tailwind CSS**, and **HTMX**, Filvora delivers real-time TMDB metadata, official age certifications, user ratings & affinity personalization engine, multi-server online playback (VidLink, VidFast 4K, AutoEmbed, VidSrc, 2Embed, NontonGo), multi-tab watch history, multi-profile user switching with Kids safety mode, season-wise viewing insights (Filvora Wrapped), and Progressive Web App (PWA) installation.

---

## ⚡ One-Click Easy Start (Windows)

After initial setup (cloning & creating the `venv`), you **do not need to use the terminal** to start Filvora.

### How to Start in One Click:
1. Double-click the **`Start Filvora.bat`** file in your project root.
2. It will automatically:
   - ✅ Verify your Python virtual environment.
   - ✅ Silently apply any pending database migrations.
   - ✅ Launch your default web browser at `http://127.0.0.1:8000/`.
   - ✅ Start the server accessible both on your PC and your local Wi-Fi / LAN network (`0.0.0.0:8000`).
3. **To stop the server**: Simply close the command window or press `Ctrl + C`.

> 💡 **Desktop Shortcut Tip**: Right-click `Start Filvora.bat` ➔ **Send to** ➔ **Desktop (create shortcut)**. You now have a desktop icon to launch your streaming platform with a single click!

---

## ✨ Key Features & Capabilities

### ⭐ 1. Interactive Star Ratings & Affinity Personalization Engine
- **Rate Any Title**: Rate movies and TV series (1–5 stars) directly from Movie/Series detail pages, your Watchlist (`/library/`), or Watch History (`/history/`) — even before streaming them.
- **Cascade Hover Animation**: Instant left-to-right gold star fill animation on hover.
- **Intelligent Recommendations**: 4–5 star ratings heavily boost corresponding genres (+5 weight) and trigger dedicated *"Because You Watched / Loved"* carousels on the homepage, while low ratings (1–2 stars) penalize disliked genres.

### 📜 2. Multi-Tab Watch History Hub (`/history/`)
- **Streamed History Tab**: Chronological rails (*Today, Yesterday, This Week, Earlier*) with exact progress bars and one-click removal.
- **Rated Titles Tab**: Dedicated responsive poster grid showcasing all your rated movies and series with live star badges and in-place rating adjustments.

### 🌟 3. Cinematic Hero Billboard & Dynamic Rails
- **Spotlight Hero**: Atmospheric backdrop banner, authentic rating scores, official age certification, and HD quality tags with responsive spacing avoiding content rail overlap.
- **One-Click Playback**: Instant stream playback from hero billboard or card hover overlays.
- **Horizontal Carousel Rails**: Drag-to-scroll navigation with anti-clipping headroom for smooth card expansion and suppressed native scrollbars.
- **Continue Watching Rail**: In-place resume with exact percentage bars and one-click removal (`×`).

### 🔍 4. Advanced Discovery & Balanced Grid Engine
- **24-Item Page Windowing (`_fetch_paginated_24`)**: Slices exactly 24 titles per page across TMDB boundaries, creating perfectly full, even rows across Desktop (6 cols), Laptop (4 cols), Tablet (3 cols), and Mobile (2 cols).
- **Dynamic Content Ratings (`_RATING_CACHE`)**: Singleton cache extracting official release certifications (`PG`, `PG-13`, `R`, `TV-MA`) for 100% rating consistency between cards and detail views.
- **Multi-Page Discover Engine**: Faceted filtering by Media Type (`movie`/`tv`), Mood, Genre, Language, Minimum Score, Certification, and Sort Order with preserved query parameters across pagination.
- **Categorized Autocomplete Search**: Live suggestions categorized into **Movies**, **TV Series**, and **People & Cast**.
- **🎲 Surprise Me Picker**: Instant intelligent recommendation jump.
- **Artist Filmographies**: Detailed actor/cast biography and filmography grids (`/person/<id>/`).

### 📺 5. Multi-Server Playback Engine (`apps/playback/`)
- **6 High-Speed Streaming Providers**: Switch streaming nodes on the fly with zero page reloads (**VidLink** [Primary Fast 1080p], **VidFast** [4K Ultra HD], **AutoEmbed**, **VidSrc** [UHD/HD], **2Embed**, **NontonGo**).
- **Direct Hover Server Switcher**: Floating pill (`Server VIDLINK ⌵`) expands a glassmorphic server switcher dropdown on cursor hover.
- **Fullscreen Overlay Preservation**: Interactive top sensors, quick server switchers, and dialogs remain mounted directly inside fullscreen video mode (`z-index: 2147483647`).
- **Playback-Driven Progress Tracking**: Records watch timestamps only when media is actively playing (`!player.paused()` and `currentTime >= 15s`). Resume prompts strictly require $\ge 30$ seconds of verified watch time.
- **Auto-Hide Controls on Pause**: Player controls and navigation auto-hide after 3.5 seconds of inactivity even when paused.
- **Keyboard Shortcuts**: <kbd>Space</kbd>/<kbd>K</kbd> (Play/Pause), <kbd>F</kbd> (Fullscreen), <kbd>M</kbd> (Mute), <kbd>←</kbd>/<kbd>→</kbd> (Seek 10s).

### 📊 6. Season-Wise Playtime & Personal Analytics (Wrapped)
- **Season Playtime Aggregation**: Computes and displays total watch hours per TV season (`Season 1: 5.4 hrs`) on season tabs.
- **5-Metric Overview**: Watch time, unique movies streamed, episodes binged, completed count, and **Avg User Rating**.
- **Genre Affinity Breakdown**: Real-time percentage bars visualizing streaming habits.
- **Filvora Wrapped**: Interactive celebratory showcase of personal milestones and top watched titles (`/analytics/`).

### 👥 7. Multi-Profile Management & Kids Mode Safety
- **Netflix-Style Profile Switcher**: Create, edit, and switch profiles per account (`/accounts/profiles/`).
- **Kids Mode Gating**: Server-side filtering enforcing safe ratings (`G`, `PG`, `TV-PG`) and hiding mature content (`R`, `TV-MA`, `NC-17`).

### 📱 8. Progressive Web App (PWA) & Mobile Shell
- **Installable PWA**: Includes `manifest.json` and Service Worker (`sw.js`) for offline caching of app shell assets.
- **Mobile Bottom Navigation**: Glassmorphic bottom bar for effortless one-thumb mobile browsing.

### ⚙️ 9. Standby Download Architecture (`apps/downloads/`)
- **Complete Pipeline Preserved**: Full backend download architecture (`DownloadJob` model, dual-mode `curl`/`requests` downloader, FFmpeg remuxer, validator, and cleanup service) preserved in standby with **34 automated tests**. User buttons are hidden from the UI since 3rd-party embed providers stream via tokenized web iframes.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend** | **Django 5.2 (Python 3.10+)** | Core application, ORM, multi-profile auth, user ratings, analytics, and recommendation engine. |
| **Frontend Rendering** | **Django Templates + Partials** | Server-rendered HTML with modular reusable component partials and strict SVG iconography. |
| **Styling & Design** | **Tailwind CSS + Plus Jakarta Sans** | Modern dark-mode streaming UI with glassmorphism and smooth star animations. |
| **Dynamic Interactivity**| **HTMX 1.9.10** | Asynchronous DOM swapping for live star rating, live search, watchlist toggles, and modal dialogs. |
| **Metadata Source** | **The Movie Database (TMDB) API** | Real-time movie/series metadata, age certifications, cast, backdrops, and recommendations. |
| **Video Playback** | **Multi-Server Streaming Nodes** | Multi-server iframe playback with 6 providers (VidLink, VidFast, AutoEmbed, VidSrc, 2Embed, NontonGo). |
| **Downloads Pipeline** | **DownloadJob Manager (Standby)** | Complete download worker pipeline, filename generator, and validation engine. |

---

## 📂 Project Directory Structure

```text
Filvora/
├── apps/
│   ├── core/                  # Home views, recommendation engine (weighted with ratings), backup command
│   ├── catalog/               # Browse, discover, mood explorer, genres, person profiles, detail views
│   ├── playback/              # Video player view, provider registry, server switcher, diagnostics
│   ├── watch/                 # WatchProgress & UserRating models, history (streamed & rated tabs), analytics
│   ├── library/               # Watchlist, custom collections & playlists with rating support
│   ├── downloads/             # Standby download pipeline, DownloadJob model & 34 tests
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
│   ├── css/main.css           # Glassmorphism, animations, star cascade hover CSS
│   ├── js/main.js             # Rail drag-scroll, keyboard shortcuts, toast engine, star rating hover engine
│   ├── manifest.json          # PWA Web App Manifest
│   └── sw.js                  # PWA Service Worker caching
├── templates/
│   ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav
│   ├── components/            # Reusable partials (movie_card, series_card, empty_state, rating_stars)
│   ├── catalog/               # Browse, discover, genres, and person detail views
│   ├── watch/                 # History (Streamed & Rated tabs) and Personal Analytics (Wrapped) templates
│   ├── downloads/             # Standby download dashboard & dialog partials
│   ├── library/               # Watchlist and custom collections manager
│   ├── accounts/              # Sign in, registration, and profile switcher
│   ├── playback/              # Immersive cinematic player view with server switcher
│   ├── 404.html               # Custom cinematic 404 error page
│   └── 500.html               # Custom cinematic 500 error page
├── Start Filvora.bat          # One-click Windows runner script
├── .env.example
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Initial Setup & Installation

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 / 3.12 recommended)
- **Git**
- A free **TMDB API Key** ([Get one here](https://www.themoviedb.org/settings/api))

---

### 2. Setup (Run Once)

```powershell
# Clone the repository
git clone https://github.com/omtiwari17/Filvora.git
cd Filvora

# Create & activate virtual environment (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment variables and insert your TMDB_API_KEY
Copy-Item .env.example .env

# Run database migrations
python manage.py migrate
```

---

### 3. Launching Filvora Everyday

Once setup is complete, you never need to activate the venv manually again:
- Simply double-click **`Start Filvora.bat`** in the project folder.

---

### 4. Running Automated Tests

Run the full automated test suite (**97 tests** across all 8 apps, 100% passing):
```powershell
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts apps.downloads
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Scope |
|---|---|---|
| <kbd>/</kbd> | Focus Search Bar | Global |
| <kbd>?</kbd> / <kbd>Shift</kbd> + <kbd>/</kbd> | Open Keyboard Shortcuts Modal | Global |
| <kbd>Esc</kbd> | Close Modals & Search Suggestions | Global |
| <kbd>Space</kbd> / <kbd>K</kbd> | Play / Pause Video | Watch Player |
| <kbd>F</kbd> | Toggle Fullscreen | Watch Player |
| <kbd>M</kbd> | Mute / Unmute Audio | Watch Player |
| <kbd>←</kbd> / <kbd>→</kbd> | Seek Backward / Forward 10 Seconds | Watch Player |

---

## 🌐 Application URL Map Reference

| Route | View Function | App | Description |
|---|---|---|---|
| `/` | `HomeView` | `apps.core` | Homepage featuring Hero billboard, personalized rails & category carousels |
| `/discover/` | `discover` | `apps.catalog` | Multi-filter discovery portal with mood chips & certification selectors |
| `/surprise-me/`| `surprise_me` | `apps.catalog` | 🎲 Instant random surprise picker |
| `/genres/` | `genres_view` | `apps.catalog` | Genre catalog portal |
| `/movies/` | `movie_browse` | `apps.catalog` | Movies catalog grid (24 titles per page) |
| `/movies/<id>/`| `movie_detail` | `apps.catalog` | Movie synopsis, cast, age rating, recommendations, ratings & one-click streaming |
| `/series/` | `series_browse` | `apps.catalog` | TV Series catalog grid (24 titles per page) |
| `/series/<id>/`| `series_detail` | `apps.catalog` | Series synopsis, season playtime badges, episode list & star ratings |
| `/person/<id>/`| `person_detail` | `apps.catalog` | Actor biography & combined filmography |
| `/watch/movie/<id>/` | `watch_movie` | `apps.playback` | Movie streaming player with 6-server switcher & beacon tracking |
| `/watch/tv/<id>/<s_num>/<ep_num>/` | `watch_episode` | `apps.playback` | TV episode streaming player with auto Next Episode |
| `/search/` | `search_results` | `apps.catalog` | Full search results grid |
| `/search/suggest/` | `search_suggest` | `apps.catalog` | HTMX categorized search suggestions dropdown |
| `/library/` | `library_list` | `apps.library` | Watchlist and custom collections manager with inline star ratings |
| `/history/` | `history_view` | `apps.watch` | Dual-tab history (Streamed History timeline & Rated Titles poster grid) |
| `/analytics/` | `analytics_view` | `apps.watch` | Viewing analytics, avg rating metric, season watch hours & Filvora Wrapped |
| `/downloads/` | `downloads_dashboard` | `apps.downloads` | Standby video download manager pipeline |
| `/accounts/profiles/` | `profiles_view` | `apps.accounts` | Multi-profile switcher & creator with Kids mode gating |

---

## 🔒 Content & Streaming Notice
Filvora does not host, store, or index copyrighted video files on its servers. The application acts as a discovery and client interface that connects authorized metadata and media stream providers. All video bandwidth is handled directly by external content delivery networks (CDNs).

---

## 📄 License
Distributed under the MIT License.