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
- **Automated Test Suite**: **113 tests** across all 8 apps (`apps.core`, `apps.catalog`, `apps.playback`, `apps.library`, `apps.watch`, `apps.tmdb`, `apps.accounts`, `apps.downloads`), **100% passing**.

---

## 2. Feature Status: What Works vs. What Is On Standby / Inactive

### 2.1 ✅ Active & 100% Working Features (v2.4 Production State)

| **High-Precision Catalog Filtering & Audience Engine** | `apps/catalog/`, `apps/tmdb/`, `templates/catalog/` | Eliminates obscure 0-vote titles from Popular/Top Rated via adaptive TMDB vote floors (`vote_count.gte >= 80` for movies, `>= 40` for TV, `>= 300` for top rated) and unreleased date filtering (`primary_release_date.lte`). Introduces Audience Segments (All Content, Live-Action / General, Kids & Family, Mature 18+/TV-MA) that cleanly separate toddler cartoons and mature films in Comedy. Features complete multi-directional genre mapping between Movies (28, 878, 53) and TV (10759, 10765), pipe-separated (`\|`) OR mood discovery, TV certification translation, dual-universe `/genres/` switcher, and 100% URL filter state preservation across tabs, rails, and pagination. |
| **True Cinema Fullscreen & Controls Overlay** | `apps/playback/`, `templates/playback/watch.html` | Hardware-composited fullscreen engine. Resolves the W3C isolated iframe spec trap via the **Embedded Fullscreen Hotspot Router** (`#embed-fullscreen-hotspot`), ensuring clicks on server player default `⛶` buttons, top bar buttons, or <kbd>F</kbd> trigger `#player-wrapper` cinema fullscreen. Full Filvora controls, persistent top pull-down notch (`#top-notch-trigger`), and server switchers remain accessible in fullscreen DOM. |
| **Snappy 3-Second Controls Auto-Hide Engine** | `templates/playback/watch.html`, `static/js/main.js` | Unconditional inactivity auto-hide sliding controls off-screen (`translateY(-100%)`) after 3 seconds of no mouse movement. Fast dismissal (1s-1.5s) on click or cursor exit. Reveal triggers via top sensor (`#top-sensor`), pull-down notch, or <kbd>C</kbd> key. Automatically suspends hide timer when interactive modals (Bookmarks, Sleep Timer) are open. |
| **1-Year Persistent Sessions & Isolated Cache Boundaries** | `config/settings.py`, `static/sw.js`, `static/js/main.js` | Long-lived Netflix-style persistent sessions (`SESSION_COOKIE_AGE = 31536000`, `SESSION_SAVE_EVERY_REQUEST = False`, `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`). SQLite converted to **Write-Ahead Logging (WAL)** mode with 30s busy timeout, preventing table lockouts during background tasks. Strict Service Worker caching boundary (`filvora-static-v3`) that only caches `/static/` assets and bypasses dynamic HTML navigation, preventing ghost sign-outs and unauthenticated cache snapshot rollbacks. |
| **Custom Timestamp Bookmarks & Scene Notes** | `apps/library/`, `apps/playback/`, `templates/playback/watch.html`, `templates/library/list.html` | Save bookmarks at exact playback seconds with personal scene notes for movies and TV episodes. Scoped per user profile (`SceneBookmark` model). Features in-player Bookmark modal (shortcut <kbd>B</kbd>), direct URL timestamp jumps (`?t=<sec>`), and a dedicated "Scene Bookmarks" tab in My Library with responsive cards, preview banners, digital timestamp badges, quick jump, and in-place deletion. |
| **Player Sleep Timer & Theater Mode Engine** | `apps/playback/`, `templates/playback/watch.html` | Sleep timer dropdown (15m, 30m, 45m, 60m, End of Episode) with live countdown badge, automatic playback fadeout/pause, and cozy sleep overlay. Theater Mode (<kbd>T</kbd>) ambient velvet black dimming focusing 100% attention on the cinema canvas. Picture-in-Picture (<kbd>P</kbd>) support with Document PiP and HTML5 Video PiP. |
| **Official Franchise & Saga Universe Rail** | `apps/tmdb/`, `apps/catalog/`, `templates/catalog/movie_detail.html` | Auto-detects if a movie belongs to an official TMDB collection/franchise (e.g. *Dune, Harry Potter, Spider-Man, John Wick, Avatar, Marvel*). Fetches all installments chronologically ordered by release date, displays saga overview and total film count, assigns chronological order badges (`#1`, `#2`, `#3`...), highlights the currently viewed film with a glowing border and `Now Viewing` indicator, and provides instant play/details actions. |
| **Official Cinematic 4K/HD Trailer Modal** | `apps/tmdb/`, `apps/catalog/`, `templates/components/trailer_modal.html` | Watch official trailers on movie detail, series detail, and homepage hero billboard without leaving the page. Built with privacy-focused YouTube embeds (`youtube-nocookie`), autoplay, zero-emoji SVG controls, instant audio/playback cutoff on dismiss, keyboard escape dismissal, and dynamic `/trailer/<media_type>/<tmdb_id>/` on-demand API fallback. |
| **Director, Creator & Interactive Cast Showcase** | `apps/catalog/`, `templates/catalog/` | Extracted official directors with dedicated badges on movie detail views, showrunners/creators on TV series detail views, and interactive clickable avatar cards linking straight to the artist's full filmography page (`/person/<id>/`) supporting both crew and cast credits. |
| **Smart TV Episode Autoplay & Up Next Overlay** | `apps/playback/`, `templates/playback/` | Intelligent episodic advance engine with season boundary rollover (smoothly transitioning from e.g. S1E8 to S2E1). Bottom-right cinematic modal with episode still thumbnail, episode title, season/episode tags, animated 8-second countdown progress bar, and instant "Play Now" action. Triggered on Video.js `ended` event and embed `postMessage` triggers ($\ge 95\%$ or $\le 25$s remaining). |
| **Profile Management Hub & Custom Avatar Themes** | `apps/accounts/`, `templates/accounts/` | Edit profile name, toggle Kids mode with animated glassmorphic iOS-style toggle switches, and select custom avatar color themes (🔴 Crimson, 🔵 Sapphire, 🟢 Emerald, 🟣 Purple, 🟡 Amber). |
| **Wi-Fi LAN Streaming & Mobile/TV QR Code Pairing** | `apps/accounts/`, `templates/accounts/`, `templates/includes/` | Dynamic local IP resolver (`get_local_ip`) displaying LAN access link (`http://192.168.1.x:8000`) in user dropdown and profile switcher. Features a 1-click **Scan to Watch** QR Code modal for instant mobile camera / Smart TV pairing without typing IP addresses. |
| **Quick Vibe & Mood Randomizer in Navbar** | `templates/includes/navbar.html`, `apps/catalog/`, `static/js/main.js`, `static/css/main.css` | Dual-mode responsive ambient discovery dropdown offering instant mood leaps (*Adrenaline Rush, Mind-Bending, Laugh Out Loud, Relax & Chill, Surprise Me*) powered by `/surprise-me/` backend engine. Features strict zero-emoji Tailwind SVG design, `@media (hover: hover) and (pointer: fine)` hover decoupling, and state-based tap-to-open / tap-to-close toggle and click-outside dismissal eliminating sticky mobile hover issues. |
| **Enhanced Watchlist / Library Filter & Sort Engine** | `templates/library/list.html`, `apps/library/` | 3-tab library hub (Watchlist, Scene Bookmarks, Custom Collections). Live client-side search input, Type selector (All / Movies / Series), Star Rating filters (All / Any Rated / 5 Stars / 4+ Stars / 3+ Stars / Unrated), multi-criteria sorting (Recently Added, Title A-Z, Title Z-A, TMDB Score, My Rating), live item count badge, and clean no-match empty state. |
| **Multi-Profile Isolation Engine (History, Ratings, Watchlist, Collections & Server Preferences)** | `apps/accounts/`, `apps/watch/`, `apps/catalog/`, `apps/playback/`, `apps/library/` | Full multi-profile isolation with session-aware active profile switching. Each profile ([`UserProfile`](file:///D:/Om/Projects/Filvora/apps/accounts/models.py#L6)) maintains its own completely independent watch history timeline rails, continue watching list, Watchlist ("My List"), scene bookmarks, custom playlists/collections, server preferences, rating scores (1–5 stars), resume timestamps, and personal analytics / Wrapped metrics. Enforces server-side `certification.lte=PG` content filtering for Kids profiles. |
| **Interactive User Ratings & Affinity Engine** | `apps/watch/`, `apps/core/`, `templates/components/` | Custom `UserRating` model (1–5 stars, unique per user profile/media). Interactive HTMX star rating widget with instant left-to-right JavaScript cascade hover animations. Weighting 4–5 star titles (+5 affinity), 3 star titles (+2 affinity), and 1–2 star titles (-2 penalty) driving "Because You Watched / Loved" suggestions per active profile. |
| **Multi-Tab Watch History & Rated Hub** | `apps/watch/`, `templates/watch/history.html` | Dual-tab history dashboard scoped per active profile featuring: (1) **Streamed History** with grouped timeline rails (*Today, Yesterday, This Week, Earlier*), progress bars, and single-item removal, and (2) **Rated Titles** tab displaying a dedicated poster grid of all user-rated content with live star badges and in-place rating adjustments. |
| **Multi-Server Online Playback & Screen-Adaptive Controls** | `apps/playback/`, `templates/playback/watch.html` | Full multi-server web player with 6 streaming providers: **VidLink** (Primary Fast 1080p HD, Default), **VidFast** (4K Ultra HD), **AutoEmbed**, **VidSrc** (UHD/HD active mirror `vidsrc.pm`), **2Embed**, **NontonGo**. Fully screen-adaptive control bar resolving mobile horizontal overflow traps: replaces raw `<select>` with responsive custom server dropdowns (`[⚡ S1 ▾]` on mobile, `[⚡ Server VIDLINK ▾]` on desktop), compact 1-row mobile icon buttons (Back, Title, Server, Next Episode, Bookmark, More, Fullscreen), a slide-up **Mobile Player Controls Sheet** (`#mobile-player-controls-sheet`) giving 1-tap thumb access to servers, sleep timer presets, and watchlist, and interactive menu suspension of controls auto-hide. Includes fullscreen overlay preservation, profile-isolated server preference memory, wildcard origin iframe permissions, universal fullscreen toggle button, resume prompt threshold ($\ge 30$s scoped per active profile), active beacon progress tracking ($\ge 15$s), and 3.5s pause auto-hide. |
| **Season Total Runtime & Analytics Engine** | `apps/catalog/`, `apps/watch/` | Aggregates individual episode runtimes per TV season via `format_season_runtime` in `apps/catalog/views.py`. Displays duration badges on season selector tabs (`Season 1 • 6h 38m`) and episode list meta headers. Aggregates user watch history by season badges in Personal Analytics & Filvora Wrapped (`/analytics/`), with 5-metric dashboard including **Avg Rating** and total rated counts for active profile. |
| **Dynamic Age Ratings Engine** | `apps/tmdb/client.py` | Automatically extracts official release certifications (`PG`, `PG-13`, `R`, `TV-MA`) from TMDB and caches them in singleton `_RATING_CACHE[media_type:tmdb_id]` across all views. Ensures 100% rating consistency between cards and detail pages. |
| **Balanced Responsive Grid Engine** | `apps/tmdb/client.py` | `_fetch_paginated_24` windowing creates perfectly full, even rows of 24 titles per page (Desktop: 4 rows of 6; Laptop: 6 rows of 4; Tablet: 8 rows of 3; Mobile: 12 rows of 2). |
| **Multi-Page Discover Engine** | `apps/catalog/` | Faceted multi-page discovery filtering by Media Type (`movie`/`tv`), Mood, Genre, Language, Score, Certification (`G`, `PG`, `PG-13`, `R`, `NC-17`), and Sort Order with preserved query parameters across pagination. |
| **Homepage Cinematic Billboard** | `templates/home/index.html` | Hero spotlight billboard with generous upper breathing space (`pt-28 sm:pt-44`) allowing backdrop artwork to shine, responsive title typography, and content shifted gracefully into the lower third (`items-end pb-6 sm:pb-10`). Tight, seamless cinematic margin (`-mt-1 sm:mt-0`) eliminates the empty black gap between CTA buttons (Play Now, Trailer, In My List, Details) and the Continue Watching rail. |
| **Mobile-First UX & Touch Architecture** | `templates/base.html`, `static/css/main.css`, `templates/playback/watch.html`, `templates/includes/navbar.html`, `templates/accounts/profiles.html` | Comprehensive mobile and touch device optimizations: (1) Universal 16px font-size CSS safeguard on mobile form inputs/selects preventing iOS Safari auto-zoom; (2) Full-bleed safe area insets (`viewport-fit=cover`, `env(safe-area-inset-top/bottom/left/right)`); (3) Mobile bottom clearance preventing content cutoff behind fixed bottom navigation; (4) Floating toast repositioning above bottom navigation; (5) Native iOS momentum flick scrolling with decoupled smooth scrolling; (6) Active tap feedback animations; (7) Mobile-safe fixed centered live search dropdown eliminating left-edge clipping; (8) Global Wi-Fi LAN QR pairing modal accessible across all pages; (9) Mobile-adapted watch player using dynamic viewport height (`100dvh`), safe-area padding, mobile-constrained top sensor (h-16), touch auto-hide delay (3.5s vs 1s), scrollable landscape bookmark modal (`max-h-[90dvh]`), direct server switcher popup on floating pill click, viewport-safe fixed dropdown on mobile, and desktop-only theater/PiP filtering; (10) Touch-visible profile edit/delete controls and watchlist deletion without hover dependency; (11) Touch-pan optimized horizontal season selector rails and episode cards. |
| **Screen-Adaptive Navbar & Cross-Device Engine** | `templates/includes/navbar.html`, `static/js/main.js` | Precision breakpoint architecture providing 100% overlap-free layouts across all viewports: Mobile (320px–767px), iPad / Tablet portrait (768px–1023px, iPad Mini, iPad Air, iPad Pro), and Desktop (1024px+). Mobile and tablets feature a dedicated `[🔍]` trigger button opening a full-width search overlay with instant HTMX live suggestions, while desktops display the inline search bar with keyboard shortcut hint (`/`). Tablet navigation links feature compact padding (`px-2.5 py-1 text-xs whitespace-nowrap`), preserving >80px of clear center margin and eliminating collisions between nav links and action buttons. |
| **Zero Emojis / Strict SVG Design** | `static/css/`, `static/js/`, `templates/` | 100% clean Tailwind SVGs across all components (metrics, badges, fallback posters, dropdowns, bat launcher, buttons). Suppressed native horizontal scrollbars on carousels/rails, rail drag-scroll, keyboard shortcuts (<kbd>F</kbd> for fullscreen, <kbd>C</kbd> for controls, <kbd>Space</kbd> for play/pause, <kbd>M</kbd> for mute, <kbd>Alt</kbd>+<kbd>S</kbd> for server switch, <kbd>B</kbd> for bookmark, <kbd>Z</kbd> for sleep timer, <kbd>T</kbd> for theater mode, <kbd>P</kbd> for PiP). |

---

### 2.2 📺 Deep Playback & Fullscreen Architecture (`apps/playback/`)

#### 2.2.1 The Fullscreen Overlay Isolation Dilemma & Permanent Solution
- **The W3C Fullscreen Isolation Trap**: Under standard browser security and W3C HTML5 Fullscreen API specs, when an `<iframe>` is placed into fullscreen directly by its internal controls, the browser renders **only the iframe element** on a hardware compositor swapchain. The entire parent document DOM (including upper controls, bookmark dialogs, and navigation) is completely omitted by the GPU renderer.
- **The Hotspot Click Router**: To provide a seamless experience where the embed player's own bottom-right `⛶` button works without breaking overlays:
  - We position `#embed-fullscreen-hotspot` (`w-16 h-16`, `bottom-0 right-0`, `z-30`) directly over the embed player's bottom-right fullscreen button.
  - Clicks hit the hotspot, executing Filvora's `toggleFullscreen()` directly with an authorized user gesture.
  - Fullscreen is requested on `#player-wrapper`, elevating the video canvas and all parent overlays into native fullscreen.
  - The `<iframe>` is excluded from native `allowfullscreen`, preventing isolated fallback.
  - Clicks on the bottom-right corner while in fullscreen cleanly exit fullscreen.

#### 2.2.2 Controls Auto-Hide & Compositor Hit-Testing
- **Compositor Hit-Testing (`#top-sensor`)**: Windows DirectComposition optimization can omit transparent `<div>` layers over hardware-accelerated video frames. Adding `background: rgba(0, 0, 0, 0.002) !important;` forces a painted compositor quad, ensuring hover and clicks near the top 136px register reliably over embed frames.
- **Persistent Pull-Down Notch (`#top-notch-trigger`)**: When the upper bar auto-hides, a styled glassmorphic notch (`[ 🔴 Controls ▾ ]`) remains visible at top-center (`z-[2147483647]`), giving the user a direct handle to drop controls back down.
- **Clean Slide Animation**: Uses `translateY(-100%)` and `opacity: 0` for complete off-screen translation without visual remnants.

#### 2.2.3 Streaming Providers Matrix:
1. **Server 1 (VidLink)** ⭐: Primary fast 1080p Full HD default server with reliable CDN routing and zero buffer stalls.
2. **Server 2 (VidFast)**: High-bitrate 4K Ultra HD & 1080p streaming node. Runs on automatic adaptive bitrate (ABR); its internal UI exposes playback speed while serving peak source resolution.
3. **Server 3 (AutoEmbed)**: Multi-source failover streaming node.
4. **Server 4 (VidSrc)**: High-definition embed mirror (`vidsrc.pm`).
5. **Server 5 (2Embed)**: Secondary backup stream node.
6. **Server 6 (NontonGo)**: Alternative multi-server backup.

---

### 2.3 🎯 High-Precision Catalog Filtering, Audience Segments & Cross-Media Architecture (`apps/catalog/`, `apps/tmdb/`)

#### 2.3.1 The TMDB Popularity Anomaly & The Adaptive Vote Floor Solution
- **The Core Problem**: TMDB calculates popularity based on rolling 24-hour hits, wiki-style edits, and daily additions on `themoviedb.org`, rather than recognized all-time or lifetime acclaim. Consequently, obscure regional indie shorts, student projects, foreign daily news broadcasts (e.g. *Tagesschau*), and reality shows with 0–3 total votes artificially spiked to the top of `/movie/popular` and `/tv/popular`. Furthermore, sorting by Highest Rated with low thresholds caused 50-vote 9.5-rated student shorts to outrank cinematic masterpieces.
- **The Solution**: 
  - Standardized catalog browsing through high-precision discover queries with adaptive vote floors:
    - **Most Popular**: `vote_count.gte >= 80` (Movies) / `vote_count.gte >= 40` (TV), returning genuine, recognized global titles.
    - **Top Rated**: `vote_count.gte >= 300` (Movies) / `vote_count.gte >= 150` (TV), with natural `vote_average.desc` ordering, preventing low-vote entries from hijacking top rated lists.
    - **Trending Today**: Directly queries native TMDB daily trending (`/trending/movie/day`, `/trending/tv/day`) with deduplication and 24-item pagination, or trending within genres/audiences.
    - **In Theaters & On The Air**: Fetches active theatrical releases (`/movie/now_playing`) and episodic shows currently broadcast (`/tv/on_the_air`).
    - **Upcoming Releases**: Surfaces anticipated upcoming releases (`primary_release_date.gte = today`, `vote_count.gte = 0`) without dropping unreleased titles.
  - **Broadcast / News & Talk Show Exclusion**: All TV series catalog and discovery queries automatically apply `without_genres = '10763,10767'`, filtering out foreign daily news broadcasts (e.g. *Tagesschau*) and late-night talk shows (*Jimmy Fallon*, *Stephen Colbert*, *Andy Cohen*).
  - **Category Isolation**: Decoupled category tabs from previous sort states so clicking Top Rated, Trending, or In Theaters immediately applies the category's natural sort and filters.

#### 2.3.2 Audience Segmentation Engine (Live-Action vs. Kids & Family vs. Mature)
- **The Core Problem**: TMDB indiscriminately classifies toddler/children animation (*Paw Patrol, Despicable Me, Minions, Toy Story, Moana*) and mature R-rated comedies (*Deadpool, Scary Movie, Jackass, Sausage Party*) under the identical Genre `35` (Comedy).
- **The Solution**: Integrated an intuitive Audience segment rail across [`movie_browse.html`](file:///D:/Om/Projects/Filvora/templates/catalog/movie_browse.html) and [`series_browse.html`](file:///D:/Om/Projects/Filvora/templates/catalog/series_browse.html):
  - **All Content** (`audience=all`): Unrestricted catalog view.
  - **Live-Action / General** (`audience=live_action`): Automatically excludes animation and children content (`without_genres = '16,10751'` for movies, `'16,10751,10762'` for TV). Browsing Comedy returns genuine live-action comedies (*Scary Movie*, *The Devil Wears Prada 2*, *Deadpool & Wolverine*, *Forrest Gump*, *Pulp Fiction*), eliminating toddler cartoons.
  - **Kids & Family** (`audience=kids_family`): Targets family animation and family-rated titles (`with_genres = '10751|16'`, `certification.lte = 'PG'`).
  - **Mature** (`audience=mature`): Targets R-rated movies (`certification = 'R'`) or TV-MA series (`certification = 'TV-MA'`).

#### 2.3.3 The Cross-Media Genre Split & Polymorphic Resolver
- **The Core Problem**: TMDB uses disjoint genre ID tables for Movies vs. TV. Movie Action is `28`, but TV Action & Adventure is `10759`; Movie Sci-Fi is `878`, but TV Sci-Fi & Fantasy is `10765`; Thriller `53` and Horror `27` do not exist in TV. Passing Movie IDs to TV endpoints returned 0 results, triggering fallback to identical mock series (*Game of Thrones*, *Stranger Things*) across all options.
- **The Solution**:
  - Implemented `_resolve_genre_for_media_type(genre_id, media_type)` with bidirectional translation maps (`MOVIE_TO_TV_GENRE_MAP`, `TV_TO_MOVIE_GENRE_MAP`).
  - `get_genres_list(media_type)` dynamically returns native TV genres (`Action & Adventure 10759`, `Sci-Fi & Fantasy 10765`, `Kids 10762`, `Reality 10764`, `War & Politics 10768`, `Western 37`) or Movie genres (`Action 28`, `Sci-Fi 878`, `Horror 27`, `Thriller 53`).
  - Updated [`genre_icon.html`](file:///D:/Om/Projects/Filvora/templates/components/genre_icon.html) with clean SVGs for all TV and movie genre IDs.
  - Recommendation engine translates TV profile affinity back to movie genres (`10759 -> 28`, `10765 -> 878`) before discovering movies.

#### 2.3.4 Mood Discovery OR-Delimited Pipe Logic & Certification Translation
- Mood discovery changed from strict comma `AND` logic to TMDB pipe `|` `OR` logic (e.g. `28|12|53` for Movie Adrenaline, `10759|80` for TV Adrenaline), eliminating 0-result drops on TV.
- Explicit form `genre_id` takes precedence over `mood` in [`discover_content`](file:///D:/Om/Projects/Filvora/apps/tmdb/client.py).
- TV certification normalizer automatically translates movie ratings (`R` $\to$ `TV-MA`, `PG-13` $\to$ `TV-14`, `PG` $\to$ `TV-PG`, `G` $\to$ `TV-G|TV-Y`).
- Added an **Active Mood Indicator** with a 1-click **Reset to All Moods** link in [`discover.html`](file:///D:/Om/Projects/Filvora/templates/catalog/discover.html).

#### 2.3.5 100% Filter State Preservation Across All Interfaces
- All category tabs, audience pills, genre pills, sort selectors, and pagination buttons preserve all active query parameters:
  `?category=...&genre=...&audience=...&sort=...&page=...`
- Upgraded [`genres.html`](file:///D:/Om/Projects/Filvora/templates/catalog/genres.html) with a dual **Movies / TV Series** universe switcher, deep-linking into `/movies/?genre=...` or `/series/?genre=...`.
- Replaced all emojis in genre lists, language dropdowns, and search suggestion avatars with strict Tailwind SVGs per Filvora Rule 4.

---

### 2.4 🔐 Authentication, Concurrency & Session Persistence Architecture (`config/settings.py`)

- **1-Year Long-Lived Sessions (Netflix-Style)**:
  - `SESSION_COOKIE_AGE = 31536000` (1 full year, 365 days).
  - `SESSION_SAVE_EVERY_REQUEST = False` (MANDATORY: Must remain `False`! When cookie age is 1 year, saving on every read request causes massive SQLite lock contention, race conditions with concurrent beacons/HTMX requests, and triggers silent session drops when `SessionStore.load()` encounters locked tables).
  - `SESSION_EXPIRE_AT_BROWSER_CLOSE = False` (Preserves session across browser and tab restarts).
  - `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, `SESSION_COOKIE_SECURE = False` (permitting local IP `192.168.1.x` and `127.0.0.1` streaming).
- **Environment & Secret Key Parity**:
  - `SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('DJANGO_SECRET_KEY') or ...` guarantees stable HMAC session hashing across CLI, background tasks, and dev server processes, preventing unexpected `request.session.flush()` logouts.
- **SQLite Concurrency & WAL Engine**:
  - Default SQLite `delete` journal mode causes table lockouts on concurrent reads/writes (e.g. running test suites or progress beacons simultaneously).
  - Configured Write-Ahead Logging: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`
  - Configured `OPTIONS['timeout'] = 30` in `DATABASES['default']` to prevent `database table is locked` exceptions.
- **Strict Service Worker Cache Boundary (`static/sw.js` — `filvora-static-v3`)**:
  - **Golden Rule**: Never cache dynamic HTML responses (`/`, `/movies/*`, `/series/*`, `/library/*`, `/accounts/*`, etc.) in the Service Worker. Dynamic HTML contains user-specific authentication state, active profile context, and CSRF tokens. Caching dynamic pages causes unauthenticated snapshot rollbacks (appearing as random sign-outs).
  - `static/sw.js` exclusively handles `/static/` assets (CSS, JS, fonts, manifest). All navigation and dynamic routes bypass the Service Worker directly to the network stack.
  - Legacy shell caches (`filvora-shell-v1`, `filvora-shell-v2`) are aggressively purged on activation and on page load in `templates/base.html`.
- **bfcache Back-Navigation Sync**:
  - Modern browsers cache navigation DOM snapshots (bfcache). When users navigate back from the video player, `pageshow` listener detects `event.persisted` and reloads the document, ensuring authenticated UI and active profiles are always up to date.

---

### 2.5 📱 Mobile-First UX, Cross-Device Breakpoints & Screen-Adaptive Engine

#### 2.5.1 The Tablet / iPad Portrait Collision Problem & Decoupled Breakpoint Matrix
- **The Core Problem**: In viewport widths between $768\text{px}$ and $1023\text{px}$ (such as iPad Mini $768\text{px}$, iPad Air $820\text{px}$, and standard tablets in portrait orientation), the inline search input bar expanded to $\approx 380\text{px}$, causing the navigation links (*Movies, Series, Discover, Genres, Vibe*) to physically collide with and wrap over the search bar and action buttons. Auth buttons ("Sign In" / "Sign Up") were squeezed into awkward two-line buttons.
- **The Breakpoint Architecture Solution**:
  - **Mobile (< 768px)**: Compact navigation bar with hamburger drawer/mobile bottom bar, icon actions, and dedicated full-width search overlay triggered by `[🔍]`.
  - **Tablet Portrait (768px – 1023px, `md:` to `lg:`)**:
    - Replaced the wide inline search input with a sleek, compact `[🔍]` icon button that opens the full-width live search overlay.
    - Compacted nav link padding to `px-2.5 py-1 text-xs whitespace-nowrap`, preserving $>80\text{px}$ of clear center breathing space.
    - Applied `whitespace-nowrap` to auth buttons, guaranteeing 1-line layout.
  - **Desktop (1024px+, `lg:`)**: Full-sized inline search bar with keyboard shortcut hint (`/`), spacious navigation links, and full action cluster.

#### 2.5.2 Watch Player Screen-Adaptive Architecture & Direct Server Selector
- **Mobile Horizontal Overflow Elimination**: Replaced the native HTML `<select>` (which overflowed narrow screens and clipped action buttons) with custom responsive glassmorphic components:
  - **Compact Mobile Server Pill (`[⚡ S1 ▾]`)**: Displays a clean 2-character server badge (`S1`, `S2`, `S3`, `S4`, `S5`, `S6`) on mobile, expanding to `[⚡ Server VIDLINK ▾]` on desktop.
  - **Viewport-Safe Dropdown (`#overlay-server-menu`)**: Styled with `fixed sm:absolute right-3 sm:right-0 top-14 sm:top-full mt-2 w-64 max-w-[calc(100vw-1.5rem)]`. On narrow mobile screens ($360\text{px}-393\text{px}$), the dropdown is anchored 12px from the right screen edge, completely preventing left-edge off-screen clipping.
  - **Direct Server Switcher Trigger (`openOverlayServerMenuDirectly`)**: Resolves the bug where clicking the floating server pill only revealed the controls bar while leaving the server menu closed. Clicks on `#quick-server-trigger` execute `openOverlayServerMenuDirectly(event)`, revealing controls and immediately opening `#overlay-server-menu` with all available streaming providers.
  - **Auto-Hide Suspension on Interaction**: `toggleOverlayServerMenu(e)` and `openOverlayServerMenuDirectly(e)` clear `hideTimeout`. The 3-second controls auto-hide timer is suspended while the user browses the server list, resuming only upon dismissal.
  - **Document Click Exclusion**: Added `#quick-server-container` to the outside-click exclusion filter, preventing click events from prematurely closing the server menu.
- **Slide-Up Mobile Player Controls Sheet (`#mobile-player-controls-sheet`)**: Accessible via the 1-tap `[⋯]` More button on mobile viewports. Provides thumb-friendly access to:
  - Full-width Video Server Failover list with active server indicators and fast CDN tags.
  - 6-preset Sleep Timer grid (Off, 15m, 30m, 45m, 1h, End of Episode).
  - Quick action grid (Watchlist toggle, Bookmark scene, Fullscreen).
  - Full safe-area inset padding (`padding-bottom: max(1.25rem, env(safe-area-inset-bottom, 0px))`).

#### 2.5.3 Homepage Cinematic Hero Billboard Lower-Third Alignment & Breathing Room
- **The Core Problem**: Vertically centering content (`items-center`) inside an 85vh hero billboard placed the text in the middle of the screen, leaving an awkward ~300px empty black void before the *Continue Watching* rail and obscuring the focal area of the backdrop artwork.
- **The Solution**:
  - Switched container alignment to `flex items-end justify-start` with generous top breathing room (`pt-28 sm:pt-36 md:pt-44`) and compact bottom padding (`pb-6 sm:pb-8 md:pb-10`).
  - Anchors the title, overview, badges, and CTA buttons (*Play Now, Trailer, In My List, Details*) into the cinematic lower third.
  - Rails container margin set to `-mt-1 sm:mt-0` with deep gradient blending (`from-gray-950 via-gray-950/45 to-transparent`), completely eliminating the gap before *Continue Watching*.

#### 2.5.4 Touch Experience, iOS Safeguards & Safe Areas
- **Universal 16px iOS Form Input Safeguard**: `#player-wrapper input, #player-wrapper select, #player-wrapper textarea` enforce `font-size: 16px !important;` on screens $\le 768\text{px}$, preventing iOS Safari from auto-zooming and breaking layouts.
- **Full-Bleed Safe Area Insets**: Base shell and player overlay utilize `viewport-fit=cover` and `env(safe-area-inset-top/bottom/left/right)` for edge-to-edge rendering around device notches, Dynamic Islands, and home indicator bars.
- **Touch-Pan Horizontal Rails**: Added `overflow-x-auto scrollbar-hide snap-x -webkit-overflow-scrolling: touch` to genre filter rails, season selector tabs, and episode cards across all browse and detail views.
- **Global Wi-Fi LAN QR Pairing Modal (`templates/components/qr_modal.html`)**: Included globally in `templates/base.html` for 1-click mobile camera / TV access without manual IP typing.

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
│   ├── settings.py            # Hardened Django settings, SQLite WAL, 1-year persistent sessions & proxy configs
│   ├── urls.py                # Main URL routing definitions
│   └── wsgi.py / asgi.py      # WSGI/ASGI application gateways
├── static/
│   ├── css/main.css           # Glassmorphism, animations, scrollbar-hide styles, star cascade hover CSS
│   ├── js/main.js             # Rail drag-scroll, keyboard shortcuts, toast engine, star rating hover, bfcache sync (v2.4)
│   ├── manifest.json          # PWA Web App Manifest
│   └── sw.js                  # PWA Service Worker caching
├── Start Filvora.bat          # Double-clickable launcher for Windows (venv check, migrations, browser launch)
└── templates/
    ├── base.html              # Base layout with navbar, footer, PWA meta & bottom nav (v2.4)
    ├── components/            # Reusable partials (movie_card, series_card, empty_state, rating_stars, trailer_modal)
    ├── catalog/               # Browse, discover, genres, franchise saga universe rail, and person detail views
    ├── watch/                 # History (Streamed & Rated tabs) and Personal Analytics (Wrapped) templates
    ├── library/               # Watchlist, Scene Bookmarks hub, and custom collections manager
    ├── accounts/              # Sign in, registration, profile switcher with QR code pairing & edit modals
    ├── playback/              # Immersive cinematic player view, notch trigger, sleep timer & autoplay overlay (v2.4)
    ├── 404.html               # Custom cinematic 404 error page
    └── 500.html               # Custom cinematic 500 error page
```

---

## 4. Key Conventions & Rules

1. **Universal Version Bump Synchronization (MANDATORY)**:
   - When bumping the application version (e.g., from `v2.3` to `v2.4`), you **MUST update all version occurrences simultaneously across the entire project**:
     - `templates/base.html`: `<title>` tag, footer logo badge, and footer release span (`v2.4.0-release`).
     - `templates/includes/navbar.html`: Logo badge next to FILVORA brand title.
     - `templates/playback/watch.html`: Player header badge next to video title.
     - `templates/accounts/login.html`: Header badge and page `<title>`.
     - `templates/accounts/register.html`: Header badge and page `<title>`.
     - `static/js/main.js`: File header docstring and Shortcuts modal title badge (`v2.4`).
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
7. **Leverage Specialized Subagents When Required (MANDATORY FOR SUPERIOR RESULTS)**:
   - For complex refactors, multi-file searches, architecture migrations, deep debugging, or parallel task execution, always employ specialized subagents (such as the `research` subagent for deep code analysis and document lookups, or `self` for isolated sub-tasks) when required. Using dedicated subagents preserves context clarity, eliminates token bloat, and delivers dramatically higher precision, speed, and overall engineering quality.

---

## 5. Useful Commands & Credentials Reference

```powershell
# Double-click launcher (or run in shell)
.\Start Filvora.bat

# Run Development Server manually
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# Run Automated Test Suite (113 tests across 8 apps)
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts apps.downloads

# Backup Local Database
.\venv\Scripts\python.exe manage.py backup_db

# Reset / Change User Password
.\venv\Scripts\python.exe manage.py changepassword moon
```

### Local Test Accounts:
- **Main User**: `moon` (Password: `1234`)
- **Superuser**: `admin` (Password: `1234`)
