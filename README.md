# 🎬 Filvora v2.0 — Next-Gen Cinema & Series Streaming Engine

[![Django](https://img.shields.io/badge/Django-5.2+-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38bdf8?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![HTMX](https://img.shields.io/badge/HTMX-1.9+-3366cc?style=for-the-badge&logo=htmx&logoColor=white)](https://htmx.org/)
[![TMDB API](https://img.shields.io/badge/TMDB-API_v3-01d277?style=for-the-badge&logo=themoviedatabase&logoColor=white)](https://www.themoviedb.org/)
[![Video.js](https://img.shields.io/badge/Video.js-Player-ff0000?style=for-the-badge&logo=video.js&logoColor=white)](https://videojs.com/)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-purple?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)

**Filvora v2.0** is a complete, production-grade cinematic movie and TV series streaming application. Built on **Django 5.2**, **Tailwind CSS**, and **HTMX**, Filvora delivers real-time TMDB metadata, official age certifications, personalized recommendation rails, multi-server playback failover, offline DRM-free video downloads, multi-profile user switching, viewing insights (Filvora Wrapped), and Progressive Web App (PWA) installation.

---

## ✨ Key Features & Capabilities

### 🌟 1. Cinematic Hero Billboard & Dynamic Rails
- **Spotlight Hero**: Atmospheric backdrop banner, authentic rating scores, official age certification, and HD quality tags.
- **One-Click Playback**: Instant stream playback from hero billboard or card hover overlays.
- **Horizontal Carousel Rails**: Drag-to-scroll navigation with anti-clipping headroom for smooth card expansion.
- **Continue Watching Rail**: In-place resume with exact percentage bars and one-click removal (`×`).

### 🧠 2. Personalization & Recommendation Engine
- **Deterministic Affinity Scoring**: Automatically learns user preferences from completed watch history and watchlist items.
- **Explainable Rails**: *"Because You Watched [Title]"* and *"Recommended For You"* rails tailored to your tastes.
- **Custom Collections**: Create and organize custom thematic playlists (e.g., "Weekend Sci-Fi Marathon").

### 🔍 3. Advanced Discovery & Categorized Search
- **Categorized Autocomplete**: Live suggestions categorized into **Movies**, **TV Series**, and **People & Cast**.
- **Mood Explorer**: Instant mood filters (`⚡ Adrenaline`, `🧠 Mind-Bending`, `🌴 Relax`, `😂 Funny`, `🥺 Emotional`, `👻 Scary`, `🌌 Escape Reality`).
- **Filter Controls**: Multi-parameter discovery by Genre, Release Year, Minimum Score, Language, and Certification.
- **🎲 Surprise Me Picker**: Instant intelligent recommendation jump.
- **Artist Filmographies**: Detailed actor/cast biography and filmography grids (`/person/<id>/`).

### 📺 4. Multi-Server Playback Engine
- **Multi-Server Provider Failover**: Switch streaming nodes on the fly without refreshing or breaking browser history (`Vidsrc`, `SuperEmbed`, `2Embed`, `EmbedSoap`, etc.).
- **Adaptive Video Player**: Video.js player with HLS streaming and sandboxed iframe fallbacks.
- **Heartbeat Beacon API**: Asynchronously records playback progress timestamps every 15 seconds.
- **Keyboard Shortcuts**: <kbd>Space</kbd>/<kbd>K</kbd> (Play/Pause), <kbd>F</kbd> (Fullscreen), <kbd>M</kbd> (Mute), <kbd>←</kbd>/<kbd>→</kbd> (Seek 10s).

### ⬇️ 5. Standalone Offline Video Download Subsystem
- **Standardized Naming**: Outputs clean standalone media files (`Movie Name (Year) [1080p].mp4` and `Series Name S01E01 [1080p].mp4`).
- **Download Queue & Manager**: Asynchronous background jobs with live progress bar polling (`/downloads/`).
- **Direct Episode Downloads**: Trigger offline downloads directly from movie detail or TV season episode lists.

### 👥 6. Multi-Profile Management & Kids Mode Safety
- **Netflix-Style Profile Switcher**: Create, edit, and switch profiles per account (`/accounts/profiles/`).
- **Kids Mode Gating**: Server-side filtering enforcing safe ratings (`G`, `PG`, `TV-PG`) and hiding mature content (`R`, `TV-MA`, `NC-17`).

### 📊 7. Personal Viewing Analytics & Filvora Wrapped
- **Viewing Metrics**: Total hours watched, unique movies streamed, episodes binged, and completed count.
- **Genre Affinity Breakdown**: Real-time percentage bars visualizing streaming habits.
- **Filvora Wrapped 2026**: Interactive celebratory showcase of personal milestones and top watched titles.

### 📱 8. Progressive Web App (PWA) & Mobile Shell
- **Installable PWA**: Includes `manifest.json` and Service Worker (`sw.js`) for offline caching of app shell assets.
- **Mobile Bottom Navigation**: Glassmorphic bottom bar for effortless one-thumb mobile browsing.

### 🔒 9. Production Hardening & Reverse Proxy Configurations
- **Reverse Proxy Ready**: Included production configs for **Caddy** (automatic HTTPS), **Nginx**, and **Docker Compose**.
- **Database Backup Command**: Run `python manage.py backup_db` for safe, lightweight database snapshots.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend** | **Django 5.2 (Python 3.10+)** | Core application, ORM, multi-profile auth, download manager, and recommendation engine. |
| **Frontend Rendering** | **Django Templates + Partials** | Server-rendered HTML with modular reusable component partials. |
| **Styling & Design** | **Tailwind CSS + Plus Jakarta Sans** | Modern dark-mode streaming UI with glassmorphism and animations. |
| **Dynamic Interactivity**| **HTMX 1.9.10** | Asynchronous DOM swapping for live search, watchlist toggles, and download queue polling. |
| **Metadata Source** | **The Movie Database (TMDB) API** | Real-time movie/series metadata, age ratings, cast, backdrops, and recommendations. |
| **Video Playback** | **Video.js + Embed Stream Providers** | Local video player with HLS streaming and multi-server embed fallbacks. |
| **Downloads Pipeline** | **DownloadJob Manager** | Asynchronous temporary chunk streaming, remuxing, and deterministic filename delivery. |

---

## 📂 Project Directory Structure

```text
Filvora/
├── apps/
│   ├── core/                  # Home views, recommendation engine, backup command
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
├── templates/
│   ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav
│   ├── components/            # Reusable partials (movie_card, series_card, empty_state)
│   ├── catalog/               # Browse, discover, genres, and person detail views
│   ├── watch/                 # History and Personal Analytics (Wrapped) templates
│   ├── downloads/             # Live polling download dashboard & partials
│   ├── library/               # Watchlist and custom collections manager
│   ├── accounts/              # Sign in, registration, and profile switcher
│   ├── 404.html               # Custom cinematic 404 error page
│   └── 500.html               # Custom cinematic 500 error page
├── .env.example
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 / 3.12 recommended)
- **Git**
- A free **TMDB API Key** ([Get one here](https://www.themoviedb.org/settings/api))

---

### 2. Setup & Installation

```powershell
# Clone the repository
git clone https://github.com/omtiwari17/Filvora.git
cd Filvora

# Create & activate virtual environment (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment variables and insert TMDB_API_KEY
Copy-Item .env.example .env

# Run database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

---

### 3. Running Automated Tests

Run the full automated test suite (55 tests across all 8 apps):
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
| `/movies/` | `movie_browse` | `apps.catalog` | Movies catalog grid |
| `/movies/<id>/`| `movie_detail` | `apps.catalog` | Movie synopsis, cast, recommendations & download button |
| `/series/` | `series_browse` | `apps.catalog` | TV Series catalog grid |
| `/series/<id>/`| `series_detail` | `apps.catalog` | Series synopsis, seasons selector & episode list |
| `/person/<id>/`| `person_detail` | `apps.catalog` | Actor biography & combined filmography |
| `/watch/movie/<id>/` | `watch_movie` | `apps.playback` | Movie streaming player with multi-server switcher |
| `/watch/tv/<id>/<s_num>/<ep_num>/` | `watch_episode` | `apps.playback` | TV episode streaming player with auto Next Episode |
| `/search/` | `search_results` | `apps.catalog` | Full search results grid |
| `/search/suggest/` | `search_suggest` | `apps.catalog` | HTMX categorized search suggestions dropdown |
| `/library/` | `library_list` | `apps.library` | Watchlist and custom collections manager |
| `/history/` | `history_view` | `apps.watch` | Chronological date-grouped watch history |
| `/analytics/` | `analytics_view` | `apps.watch` | Viewing analytics & Filvora Wrapped 2026 showcase |
| `/downloads/` | `downloads_dashboard` | `apps.downloads` | Standalone video download pipeline & job queue |
| `/accounts/profiles/` | `profiles_view` | `apps.accounts` | Multi-profile switcher & creator |

---

## 🔒 Content & Streaming Notice
Filvora does not host, store, or index copyrighted video files on its servers. The application acts as a discovery and client interface that connects authorized metadata and media stream providers. All video bandwidth is handled directly by external content delivery networks (CDNs).

---

## 📄 License
Distributed under the MIT License.