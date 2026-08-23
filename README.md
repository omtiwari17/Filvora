# 🎬 Filvora v2.0 — Next-Gen Cinema & Series Streaming Engine

[![Django](https://img.shields.io/badge/Django-5.2+-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38bdf8?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![HTMX](https://img.shields.io/badge/HTMX-1.9+-3366cc?style=for-the-badge&logo=htmx&logoColor=white)](https://htmx.org/)
[![TMDB API](https://img.shields.io/badge/TMDB-API_v3-01d277?style=for-the-badge&logo=themoviedatabase&logoColor=white)](https://www.themoviedb.org/)
[![Video.js](https://img.shields.io/badge/Video.js-Player-ff0000?style=for-the-badge&logo=video.js&logoColor=white)](https://videojs.com/)

**Filvora v2.0** is a personal, cinematic movie and TV-series discovery and streaming web application. Built on **Django**, **Tailwind CSS**, and **HTMX**, Filvora offers a fast streaming experience with real-time metadata, live search, multi-server playback failover, watch progress tracking, and interactive watchlists without the complexity of a heavy SPA framework.

---

## ✨ Features & Highlights

### 🌟 1. Cinematic Hero Billboard & Dynamic Rails
- **Spotlight Hero**: Atmospheric backdrop banner, rating score, `4K Ultra HD`, `Dolby Atmos`, and `HDR10+` quality tags.
- **One-Click Playback**: Play immediately from the hero banner or any card hover overlay.
- **Horizontal Carousel Rails**: Smooth left/right navigation arrows, drag-to-scroll, mouse-wheel horizontal panning, and touch gestures.
- **Continue Watching Rail**: Resumes playback from where you left off with accurate progress percentages.

### 🔍 2. Live Instant Search & Auto-Suggestions
- **Debounced HTMX Search**: Real-time dropdown suggestions with thumbnails, release year, TMDB score, and category badges.
- **Keyboard Shortcut (`/`)**: Press `/` anywhere to instantly focus and search across the entire catalog.
- **Full Search Results**: Dedicated search results page with filterable movie and series grids.

### 📺 3. Robust Multi-Server Playback Engine
- **Multi-Server Provider Failover**: Switch between streaming servers on the fly without refreshing or breaking browser history (`Server Vidsrc`, `Server SuperEmbed`, `Server 2Embed`, `Server EmbedSoap`, etc.).
- **Adaptive Video.js Player**: Integrated local Video.js with fantasy theme, HLS support, and iframe embed fallback.
- **Beacon API Watch Progress**: Background heartbeat saving playback timestamps every 15 seconds to calculate progress without database strain.
- **Keyboard Player Controls**: Global shortcuts (<kbd>Space</kbd>/<kbd>K</kbd> to Play/Pause, <kbd>F</kbd> for Fullscreen, <kbd>M</kbd> to Mute, <kbd>←</kbd>/<kbd>→</kbd> to Seek 10s).

### 📑 4. Interactive Watchlist (My List)
- **Async HTMX Toggles**: Add or remove titles from cards, hero banners, or detail pages without page reloads.
- **Watchlist Tabs**: Quick filter by **All**, **Movies**, or **TV Series** with a live item counter.
- **Toast Feedback**: Non-intrusive slide-in notifications (`✓ Updated your Watchlist`).

### 📱 5. Native App-Style Mobile Navigation
- **Glassmorphic Bottom Navigation**: Fixed bottom bar on mobile screens for effortless one-thumb navigation between Home, Movies, Series, My List, and Search.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend** | **Django 5.2 (Python 3.12)** | Core application, ORM, authentication, routing, and caching. |
| **Frontend Rendering** | **Django Templates** | Server-rendered HTML with modular template partials. |
| **Styling & Design** | **Tailwind CSS + Plus Jakarta Sans** | Modern dark-mode streaming UI with glassmorphism and animations. |
| **Dynamic Interactivity**| **HTMX 1.9.10** | Asynchronous DOM swapping for live search, watchlists, and seasons. |
| **Metadata Source** | **The Movie Database (TMDB) API** | Real-time movie/series metadata, cast, crew, backdrops, and recommendations. |
| **Video Playback** | **Video.js + Embed Stream Providers** | Local video player with HLS streaming and multi-server embed fallbacks. |
| **Database** | **SQLite (Dev) / PostgreSQL (Prod)** | Stores user accounts, watch history, playback progress, and watchlist items. |

---

## 📂 Project Directory Structure

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
├── templates/
│   ├── base.html              # Base layout with Plus Jakarta Sans & mobile bottom nav
│   ├── includes/
│   │   └── navbar.html        # Glassmorphic top bar with v2.0 branding & live search
│   ├── home/
│   │   └── index.html         # Homepage with Hero billboard and category rails
│   ├── catalog/
│   │   ├── movie_browse.html  # Movies grid with v2.0 hover overlays
│   │   ├── movie_detail.html  # Movie synopsis, cast, and recommendations
│   │   ├── series_browse.html # TV series grid
│   │   ├── series_detail.html # Series synopsis, seasons, and episode list
│   │   ├── search_results.html# Full search results grid
│   │   └── partials/          # HTMX search suggestions and episode list partials
│   ├── playback/
│   │   └── watch.html         # Fullscreen video player with server switcher
│   ├── library/
│   │   └── list.html          # My List watchlist with category filter tabs
│   └── accounts/
│       ├── login.html         # User sign in form
│       └── register.html      # User registration form
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **Git**
- A free **TMDB API Key** ([Get one here](https://www.themoviedb.org/settings/api))

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/Filvora.git
cd Filvora
```

### 3. Create and Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-super-secret-django-key
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_READ_ACCESS_TOKEN=your_tmdb_bearer_token_here
```

### 6. Run Database Migrations
```bash
python manage.py migrate
```

### 7. Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

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

## 🌐 Application URL Map

| Route | View | Description |
|---|---|---|
| `/` | `HomeView` | Homepage featuring Hero billboard & category rails |
| `/movies/` | `movie_browse` | Browse all trending & popular movies |
| `/movies/<id>/` | `movie_detail` | Movie overview, cast rail, and recommendations |
| `/series/` | `series_browse` | Browse trending TV series |
| `/series/<id>/` | `series_detail` | Series overview, seasons selector, and episode list |
| `/series/<id>/season/<num>/` | `season_episodes` | HTMX partial returning episode cards for selected season |
| `/watch/movie/<id>/` | `watch_movie` | Movie stream player with multi-server switcher |
| `/watch/tv/<id>/<s_num>/<ep_num>/` | `watch_episode` | TV episode stream player with auto Next Episode |
| `/search/` | `search_results` | Full search results grid |
| `/search/suggest/` | `search_suggestions`| HTMX live search suggestions dropdown |
| `/library/` | `library_list` | User's personal Watchlist with category filter tabs |
| `/library/toggle/` | `toggle_item` | HTMX endpoint to add/remove title from watchlist |
| `/progress/save/` | `save_progress` | Beacon API endpoint to store playback progress timestamps |
| `/accounts/login/` | `login_view` | User login |
| `/accounts/register/` | `register_view` | User registration |

---

## 🔒 Content & Streaming Architecture Notice
Filvora does not host, store, or index copyrighted video files on its servers. The application acts as a discovery and client interface that connects authorized metadata and media stream providers. All video bandwidth is handled directly by external content delivery networks (CDNs).

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.