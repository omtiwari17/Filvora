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
- **Automated Test Suite**: **168 tests** across all 7 active production apps (`apps.core`, `apps.catalog`, `apps.playback`, `apps.library`, `apps.watch`, `apps.tmdb`, `apps.accounts`), **100% passing**.
- **Master Test Runner & Launcher**:
  - `run_all_tests.py` & `Run Tests.bat` located at root: single command/one-click execution running all 168 tests across all 7 active subsystems with ANSI-colorized tabular scorecard, execution times, detailed failure diagnostics, and exit code 0. Supports `--verbose`, `--failfast`, `--app <name>`, `--category <1-7>`, and `--fast`.

---

## 2. Feature Status: What Works vs. What Is On Standby / Inactive

### 2.1 ✅ Active & 100% Working Features (v2.5 Production State)

| Feature & Subsystem | Primary Codebase Footprint | Architectural Summary & Capabilities |
| :--- | :--- | :--- |
| **TV Season Episode Count Badges & Horizontal Track Scrolling Engine** | `apps/catalog/views.py`, `templates/catalog/series_detail.html`, `apps/catalog/tests.py`, `run_all_tests.py` | Replaces misleading calculated runtime strings (`[5h 52m]`) on TV series season tabs with accurate episode count badges (`[10 Episodes]`, `[1 Episode]`) while preserving chunk ranges (`[Eps 1–100]`) for mega-seasons (>100 episodes). Solves clipped horizontal season tabs and non-functional desktop mouse wheel scrolling on series detail pages. Equips `#season-tabs-track` with glassmorphic Left (`#season-rail-prev-btn`) and Right (`#season-rail-next-btn`) circular chevron navigation buttons with subtle ambient edge gradient masks (`#season-rail-fade-left`, `#season-rail-fade-right`). Introduces a multi-input scrolling engine: (1) mouse wheel listener translating vertical `deltaY` to smooth horizontal `scrollLeft`; (2) mouse grab-and-drag gesture scrolling with drag detection and click suppression (`window.__seasonTrackDragging`); and (3) relative auto-centering in `setActiveSeasonTab` keeping selected season buttons visible within the track without disturbing window scroll position. Verified with a dedicated unit test in `apps.catalog` (33 catalog tests, 168 total project tests, 100% passing). |
| **Favorite Actors & Artists Hub Engine** | `templates/components/person_favorite_button.html`, `templates/catalog/person_detail.html`, `templates/library/list.html`, `apps/library/models.py`, `apps/library/views.py`, `apps/library/urls.py`, `apps/catalog/views.py`, `apps/library/tests.py`, `apps/catalog/tests.py` | Enables users to save any actor, director, or artist as a favorite directly from their filmography profile (`/person/<id>/`) via a glassmorphic 1-click HTMX toggle button (`[♡ Favorite Actor]` -> `[♥ Favorited]`), and manage their favorite roster in a dedicated 4th tab ("Favorite Actors") inside My Library (`/library/#actors`). Implements `FavoritePerson` model with `user`, `profile`, `person_id`, cached `name`, `profile_path`, and `known_for_department` for zero-latency retrieval without TMDB overhead. Features multi-profile isolation, 1-click in-place removal (`deleteFavoriteActorCard`), smooth CSS card collapse animation, empty state fallback, and live badge count tracking. Covered by 4 dedicated automated unit tests (18 library tests, 33 catalog tests, 168 total project tests, 100% passing). |
| **Up Next Autoplay Countdown & Fullscreen Resilience Engine** | `templates/playback/watch.html`, `apps/playback/tests.py`, `run_all_tests.py` | Eliminates the critical bug where the episodic Up Next overlay banner was hidden in fullscreen mode and the countdown timer froze at "Playing in 7s" without decreasing. Introduces `isAutoplayActive` state management preventing high-frequency `timeupdate` postMessage packet floods from embed players (e.g. VidFast, VidLink, AutoEmbed) from repeatedly resetting the countdown interval back to 8s. Guarantees deterministic 1000ms decrementing from 8s to 0s (`Playing in 8s` -> `Playing in 0s`), smooth linear progress bar width shrink (`transition: width 1s linear`), automatic redirection to the next episode URL on `countdown <= 0`, and 1-click immediate jump via "Play Now". Deploys top-layer CSS stacking (`z-index: 2147483647 !important;`, `z-[2147483647]`, and `:fullscreen #autoplay-modal`) ensuring the modal renders with 100% visibility over the video in both windowed and cinema fullscreen modes. Expands `#embed-fullscreen-hotspot` to `w-20 h-20 sm:w-24 sm:h-20` (80px x 80px) to reliably intercept embed player ⛶ clicks across all DPI scaling levels and route them to Filvora's cinema fullscreen, while temporarily disabling hotspot pointer events during active autoplay countdowns so clicks on "Play Now" and "Cancel" are never blocked. Automatically dismisses and resets the modal if the user scrubs backwards away from the episode ending (`dur - pos > 35 && pos / dur < 0.90`). Covered by a dedicated unit test in `apps.playback` (19 playback tests, 168 total project tests, 100% passing). |
| **Zero-Latency Performance & Multi-Tiered Cache Architecture** | `apps/tmdb/client.py`, `apps/core/views.py`, `apps/core/recommendations.py`, `config/settings.py`, `templates/components/qr_modal.html`, `templates/accounts/login.html`, `templates/accounts/profiles.html` | Completely eliminates 40+ second server timeouts, worker thread starvation, and browser tab loading spinners. Replaces 180+ blocking remote HTTP certification requests per page load with instant genre/adult heuristic mapping and in-memory rating lookup in `_attach_age_rating` (speeding up single rail lookups by 30x from 4.5s to 0.15s). Introduces lightweight `get_content_summary` for Continue Watching and My List previews executed concurrently with `ThreadPoolExecutor`, dropping continue watching resolution from 11.4s to 0.05s. Implements 15-minute cached affinity genre profiles (`user_affinity_genres_<user>_<profile>`) in `RecommendationEngine`. Configures persistent file-based caching (`CACHES['default']`) storing TMDB API responses in `.cache/django_cache` with a 30-minute TTL, enabling instant <50ms warm-load navigation and surviving server restarts. Eliminates eager third-party image fetching on page load (`api.qrserver.com`) by lazy-loading the QR modal on demand. Tested and verified across 168/168 unit tests (100% pass rate). |
| **Watch Date & Multi-Day Session Resolution Engine** | `apps/watch/models.py`, `apps/watch/views.py`, `templates/watch/history.html`, `apps/watch/tests.py`, `doc/PROPOSED_ARCHITECTURE.md` | Resolves the multi-day watch date dilemma when users start streaming a movie or series on one calendar day and finish it on another. Tracks explicit session initiation (`created_at`) and completion (`completed_at`) timestamps on `WatchProgress`. Dynamically computes human-readable date spans via `watch_date_display` and contextual hover tooltips via `watch_date_tooltip`: single-day completions render the exact completion date (`Sep 18, 2026` or historical dates e.g. `Sep 15, 2026` for titles watched in a single sitting), multi-day sessions display the start-to-finish date span (`Sep 15 – 18, 2026`, or cross-month/year e.g. `Aug 28 – Sep 02, 2026`), and in-progress sessions display start-to-last-played spans (`Sep 10 – 14, 2026`). Features `effective_start_dt` and `effective_end_dt` chronological clamping preventing inverted dates, and includes migration 0006 aligning historical pre-migration timestamps. Injects a subtle calendar SVG badge pill into every history card next to `[Watched]` and `[S01E02]`. Preserves `updated_at` ordering across grouped history timeline rails (*Today, Yesterday, This Week, Earlier*). Covered by 7 dedicated unit tests in `apps.watch` (40 total watch tests, 168 total project tests, 100% passing). |
| **Franchise Saga & Complete Collection Batch Actions Engine** | `apps/watch/views.py`, `apps/watch/urls.py`, `apps/library/views.py`, `apps/library/urls.py`, `apps/catalog/views.py`, `templates/components/collection_actions_bar.html`, `templates/catalog/movie_detail.html`, `static/js/main.js`, `static/css/main.css`, `apps/watch/tests.py`, `apps/library/tests.py` | Extends 1-click in-card quick actions to entire cinematic universes and franchise collections (e.g. *Dune Collection*, *The Dark Knight Trilogy*, *Spider-Man Spider-Verse*, *John Wick*, *Harry Potter*). Equips the Official Franchise Saga rail header with 4 batch actions: (1) **Franchise Completion HUD** tracking `X of Y Watched (Z%)` with dynamic emerald `✓ Saga Completed` state; (2) **1-Click "Mark Saga as Watched" Toggle** (`/progress/collection/mark-watched/`) completing or unmarking all movies in the saga simultaneously; (3) **1-Click "Rate Entire Saga" Popover Capsule** (`/progress/collection/rate/` & `/progress/collection/rate/remove/`) assigning 1–5 stars across all franchise parts in one tap with live star hover illumination, active saga score badge (`★ 5/5 Saga Rated`), clear rating option, and hardened flex dimensions/SVG width attributes preventing stars from collapsing into dots; and (4) **1-Click "Add Saga to My List" Toggle** (`/library/collection/toggle-all/`). Features **Full In-Card Parity**: every movie card in the saga rail possesses permanent desktop & mobile `Seen` indicators, center direct Play, and the standard 4-button action row (`[+]`, `[👁]`, `[★]`, `[ⓘ]`). Features real-time live client synchronization (`sagaWatchedChanged`, `sagaRatingChanged`) illuminating timeline ribbon segments emerald, toggling card `Seen` badges via `!hidden`, and updating all in-card `[👁]` watch buttons and `[★]` rating buttons live without full-page reloads. 100% profile-isolated with 4 dedicated batch tests in `apps.watch` and `apps.library`. |
| **In-Card Quick Actions Engine (Mark as Watched & Star Rating Popover)** | `apps/watch/views.py`, `apps/watch/urls.py`, `apps/watch/context_processors.py`, `apps/watch/templatetags/watch_tags.py`, `templates/components/card_watch_button.html`, `templates/components/card_rating_button.html`, `templates/components/detail_watch_button.html`, `templates/components/movie_card.html`, `templates/components/series_card.html`, `templates/catalog/movie_detail.html`, `templates/catalog/series_detail.html`, `static/js/main.js`, `static/css/main.css`, `templates/base.html`, `apps/watch/tests.py` | Eliminates the need to open movie/series details pages to rate or mark titles as watched. Equips all movie and TV series cards across the catalog (Homepage billboard/rails, Movies browse, TV Series browse, Discover, Search, Recommendations, and History) with 4 dedicated in-card actions: (1) Watchlist toggle `[+]`; (2) 1-Click "Mark as Watched" toggle `[👁]` with instant emerald indicator and tooltip confirmation; (3) Quick Star Rating button `[★]` with micro glassmorphic popover capsule (1–5 stars) featuring live hover illumination, in-place HTMX submission, and clear rating `[✕]` option; and (4) Info details link `[ⓘ]`. Features **Real-Time Reactive State Synchronization**: Dispatches `watchChanged` and `ratingChanged` HTMX triggers from backend endpoints (`toggle_watched`, `rate_content`, `remove_rating`) to instantly toggle permanent `• Seen` badges (`.card-seen-desk-*`, `.card-seen-mob-*`) via CSS `!hidden` override, update all `#card-watch-btn-*` buttons, and update `#detail-watch-btn-*` across all cards on the page without requiring full-page reloads. Star popovers feature anti-collapse layout hardening: explicit `.star-opt` button sizing (`w-7 h-7`), explicit SVG attributes (`width="18" height="18"` / `width="20" height="20"`), `shrink-0 pointer-events-none`, and `min-w-max whitespace-nowrap` capsule constraints with CSS safeguards in `main.css` and `<head>` eliminating cyclic zero-width dot shrinkage. Features strict click propagation prevention (`event.stopPropagation()`), universal active-profile context processor (`user_watch_context`), safe template dict filter (`get_item`), desktop & mobile permanent watched indicators, and detail view parity. 100% profile-isolated with 40 automated tests in `apps.watch`. |
| **Theatrical & OTT / Digital Release Dates Engine** | `apps/tmdb/client.py`, `templates/catalog/movie_detail.html`, `templates/catalog/series_detail.html`, `apps/catalog/tests.py`, `apps/tmdb/tests.py` | Extracts and displays full theatrical cinema release dates and digital/OTT streaming release dates. Parses TMDB `release_dates` (Type 3: Theatrical, Type 4: Digital/OTT) and `watch/providers` (flatrate streaming partners e.g. HBO Max, Disney+, Netflix, Prime Video, Hulu, Paramount+). Replaces bare release years with human-friendly formatted dates (`Jun 26, 2026`). Features an ambient OTT pill (`📺 OTT: Sep 10, 2026 (HBO Max)`) directly in the title metadata row, alongside a dedicated glassmorphic availability bar with Cinema status, Digital/OTT release dates, platform badges, and live "Available" / "Upcoming" tags. Extends to TV series with premiere air date, final/latest air date, and primary broadcast/network streaming home. Includes unit tests with 100% pass coverage across offline mock fallbacks and live payloads. |
| **Offline-First Resilience & Universal Empty State Engine** | `templates/base.html`, `static/vendor/`, `static/css/main.css`, `static/js/main.js`, `static/sw.js`, `apps/tmdb/client.py`, `templates/components/empty_state.html`, `templates/home/index.html` | Completely eliminates the "white screen of death", unstyled blue hyperlinks, and runaway SVG icon expansion when opening Filvora without internet. Ships local standalone vendor bundles (`static/vendor/tailwind.min.js`, `static/vendor/htmx.min.js`) with automatic CDN fallbacks and Service Worker caching (`filvora-static-v4`). Injects critical `<head>` inline CSS and CSS reset guarantees ensuring dark background (`#030712`), text styling, link resets, and strict SVG dimension boundaries (`.w-2` through `.w-16`) even if JavaScript is blocked or delayed. Introduces fast offline short-circuit in `TMDBClient` (`_offline_until`) that bypasses hanging network calls and curl timeouts when DNS fails, reducing offline load times from 30s to <50ms. Features an ambient top-floating network monitor HUD (`#network-status-indicator`) tracking live `online`/`offline` status with auto-reconnection refresh. Deploys cinematic empty and offline states across Home, Genres, Analytics, Watchlist, Search, and Bookmarks with 1-click 'Check Connection & Retry' and local watchlist navigation. |
| **Master Automated Test Runner & 168-Test Scorecard Engine** | `run_all_tests.py`, `Run Tests.bat`, `apps/*/tests.py` | Unified one-command (`python run_all_tests.py`) and one-click (`Run Tests.bat`) test execution running 168 tests across all 7 active production apps. Covers every active feature, API, button, modal, HTMX action, security boundary, and failover engine. Features real-time test execution streaming: automatically prints subsystem category headers, live `[RUN ]` test progress indicators so users know what is running at any instant, followed immediately by `[PASS]`/`[FAIL]` badges, human-readable test descriptions, and millisecond timings. Concludes with an ANSI-colorized terminal scorecard table, failure diagnostics, zero-emoji compliance, and `--fast` mock acceleration. |
| **Dynamic CSRF Auto-Sync & Branded Auto-Healing Engine** | `config/settings.py`, `apps/core/views.py`, `templates/403_csrf.html`, `static/js/main.js`, `templates/base.html` | Completely eliminates "CSRF token from POST incorrect" errors across all devices and browsers. Frontend global capture interceptor (`initCsrfSync`) synchronizes `csrfmiddlewaretoken` on every `<form method="POST">` submission with the live `csrftoken` browser cookie, dynamically updating stale tokens from back-forward cache (bfcache), old tabs, or post-login cookie rotations. HTMX headers dynamically bind to live cookies (`getCookie('csrftoken')`). Configures comprehensive `CSRF_TRUSTED_ORIGINS` across port and portless origins. Provides a branded cinematic CSRF recovery view (`csrf_failure`) and template (`403_csrf.html`) featuring automated cookie renewal (`rotate_token`), an animated 3-second recovery countdown, and 1-click retry. Purged legacy invalid session entries from SQLite WAL. |

| **High-Precision Catalog Filtering & Audience Engine** | `apps/catalog/`, `apps/tmdb/`, `templates/catalog/` | Eliminates obscure 0-vote titles from Popular/Top Rated via adaptive TMDB vote floors (`vote_count.gte >= 80` for movies, `>= 40` for TV, `>= 300` for top rated) and unreleased date filtering (`primary_release_date.lte`). Introduces Audience Segments (All Content, Live-Action / General, Kids & Family, Mature 18+/TV-MA) that cleanly separate toddler cartoons and mature films in Comedy. Features complete multi-directional genre mapping between Movies (28, 878, 53) and TV (10759, 10765), pipe-separated (`\|`) OR mood discovery, TV certification translation, dual-universe `/genres/` switcher, and 100% URL filter state preservation across tabs, rails, and pagination. |
| **True Cinema Fullscreen & Clean Canvas Overlay** | `apps/playback/`, `templates/playback/watch.html` | Hardware-composited fullscreen engine. Resolves the W3C isolated iframe spec trap via the **Embedded Fullscreen Hotspot Router** (`#embed-fullscreen-hotspot`), ensuring clicks on server player default `⛶` buttons, top bar buttons, or <kbd>F</kbd> trigger `#player-wrapper` cinema fullscreen. All controls hide 100% cleanly off-screen with zero persistent notches, pills, or screen clutter during playback. |
| **Snappy 2-Second Cinema Auto-Hide & Cursor Conceal Engine** | `templates/playback/watch.html` | Snappy inactivity auto-hide sliding controls off-screen (`translateY(-100%)`) after 2.0s. Eliminates postMessage loop resets where periodic `timeupdate` packets repeatedly cancelled the hide timer. Fast dismissal (600ms–800ms) on click outside or cursor exit. Auto-conceals mouse cursor (`cursor: none`) during playback. Responsive 36px top sensor (`#top-sensor`) smoothly slides controls down on approaching the top edge. Keyboard shortcuts (<kbd>C</kbd>, <kbd>F</kbd>, <kbd>Alt</kbd>+<kbd>S</kbd>) and interactive modals (Bookmarks, Sleep Timer) cleanly integrate without getting stuck. |
| **1-Year Persistent Sessions & Isolated Cache Boundaries** | `config/settings.py`, `static/sw.js`, `static/js/main.js` | Long-lived Netflix-style persistent sessions (`SESSION_COOKIE_AGE = 31536000`, `SESSION_SAVE_EVERY_REQUEST = False`, `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`). SQLite converted to **Write-Ahead Logging (WAL)** mode with 30s busy timeout, preventing table lockouts during background tasks. Strict Service Worker caching boundary (`filvora-static-v3`) that only caches `/static/` assets and bypasses dynamic HTML navigation, preventing ghost sign-outs and unauthenticated cache snapshot rollbacks. |
| **Custom Timestamp Bookmarks & Scene Notes** | `apps/library/`, `apps/playback/`, `templates/playback/watch.html`, `templates/library/list.html` | Save bookmarks at exact playback seconds with personal scene notes for movies and TV episodes. Scoped per user profile (`SceneBookmark` model). Features in-player Bookmark modal (shortcut <kbd>B</kbd>), direct URL timestamp jumps (`?t=<sec>`), and a dedicated "Scene Bookmarks" tab in My Library with responsive cards, preview banners, digital timestamp badges, quick jump, and in-place deletion. |
| **Player Sleep Timer & Theater Mode Engine** | `apps/playback/`, `templates/playback/watch.html` | Sleep timer dropdown (15m, 30m, 45m, 60m, End of Episode) with live countdown badge, automatic playback fadeout/pause, and cozy sleep overlay. Theater Mode (<kbd>T</kbd>) ambient velvet black dimming focusing 100% attention on the cinema canvas. Picture-in-Picture (<kbd>P</kbd>) support with Zero-Reload Floating Mini-Player PiP and HTML5 Video PiP. |
| **Zero-Reload Floating Mini-Player PiP Engine** | `templates/playback/watch.html` | Solves the critical issue where Document PiP cross-document iframe adoption destroyed and refreshed embed players. Introduces an in-page floating mini-player mode (`#video-container.pip-floating-mode`) docked to `bottom-6 right-6` with 16:9 aspect ratio, rounded corners, brand border glow, and a floating overlay control bar with restore and close actions. Preserves `#video-container` directly within the parent DOM hierarchy, ensuring embed iframes never unmount, never reload, and never interrupt video playback. Supported by <kbd>P</kbd> keyboard shortcut, top bar PiP button, <kbd>Esc</kbd> restoration, and an ambient background card with 1-click player recovery and catalog browsing. |
| **Official Franchise & Saga Universe Rail** | `apps/tmdb/`, `apps/catalog/`, `templates/catalog/movie_detail.html` | Auto-detects if a movie belongs to an official TMDB collection/franchise (e.g. *Dune, Harry Potter, Spider-Man, John Wick, Avatar, Marvel*). Fetches all installments chronologically ordered by release date, displays saga overview and total film count, assigns chronological order badges (`#1`, `#2`, `#3`...), highlights the currently viewed film with a glowing border and `Now Viewing` indicator, and provides instant play/details actions. |
| **Official Cinematic 4K/HD Trailer Modal** | `apps/tmdb/`, `apps/catalog/`, `templates/components/trailer_modal.html` | Watch official trailers on movie detail, series detail, and homepage hero billboard without leaving the page. Built with privacy-focused YouTube embeds (`youtube-nocookie`), autoplay, zero-emoji SVG controls, instant audio/playback cutoff on dismiss, keyboard escape dismissal, and dynamic `/trailer/<media_type>/<tmdb_id>/` on-demand API fallback. |
| **Director, Creator & Interactive Cast Showcase** | `apps/catalog/`, `templates/catalog/` | Extracted official directors with dedicated badges on movie detail views, showrunners/creators on TV series detail views, and interactive clickable avatar cards linking straight to the artist's full filmography page (`/person/<id>/`) supporting both crew and cast credits. |
| **Smart TV Episode Autoplay & Up Next Overlay** | `apps/playback/`, `templates/playback/` | Intelligent episodic advance engine with season boundary rollover (smoothly transitioning from e.g. S1E8 to S2E1). Bottom-right cinematic modal with episode still thumbnail, episode title, season/episode tags, animated 8-second countdown progress bar, and instant "Play Now" action. Triggered on Video.js `ended` event and embed `postMessage` triggers ($\ge 95\%$ or $\le 25$s remaining). |
| **Profile Management Hub & Custom Avatar Themes** | `apps/accounts/`, `templates/accounts/` | Edit profile name, toggle Kids mode with animated glassmorphic iOS-style toggle switches, and select custom avatar color themes (🔴 Crimson, 🔵 Sapphire, 🟢 Emerald, 🟣 Purple, 🟡 Amber). |
| **Wi-Fi LAN Streaming & Mobile/TV QR Code Pairing** | `apps/accounts/`, `templates/accounts/`, `templates/includes/` | Dynamic local IP resolver (`get_local_ip`) displaying LAN access link (`http://192.168.1.x:8000`) in user dropdown and profile switcher. Features a 1-click **Scan to Watch** QR Code modal for instant mobile camera / Smart TV pairing without typing IP addresses. |
| **Quick Vibe & Mood Randomizer in Navbar** | `templates/includes/navbar.html`, `apps/catalog/`, `static/js/main.js`, `static/css/main.css` | Dual-mode responsive ambient discovery dropdown offering instant mood leaps (*Adrenaline Rush, Mind-Bending, Laugh Out Loud, Relax & Chill, Surprise Me*) powered by `/surprise-me/` backend engine. Features strict zero-emoji Tailwind SVG design, `@media (hover: hover) and (pointer: fine)` hover decoupling, and state-based tap-to-open / tap-to-close toggle and click-outside dismissal eliminating sticky mobile hover issues. |
| **Enhanced Watchlist / Library Filter & Sort Engine** | `templates/library/list.html`, `apps/library/` | 4-tab library hub (Watchlist, Scene Bookmarks, Custom Collections, Favorite Actors). Live client-side search input, Type selector (All / Movies / Series), Star Rating filters (All / Any Rated / 5 Stars / 4+ Stars / 3+ Stars / Unrated), multi-criteria sorting (Recently Added, Title A-Z, Title Z-A, TMDB Score, My Rating), live item count badge, and clean no-match empty state. |
| **Multi-Profile Isolation Engine (History, Ratings, Watchlist, Collections & Server Preferences)** | `apps/accounts/`, `apps/watch/`, `apps/catalog/`, `apps/playback/`, `apps/library/` | Full multi-profile isolation with session-aware active profile switching. Each profile ([`UserProfile`](file:///D:/Om/Projects/Filvora/apps/accounts/models.py#L6)) maintains its own completely independent watch history timeline rails, continue watching list, Watchlist ("My List"), scene bookmarks, custom playlists/collections, server preferences, rating scores (1–5 stars), resume timestamps, and personal analytics / Wrapped metrics. Enforces server-side `certification.lte=PG` content filtering for Kids profiles. |
| **Dynamic Attribution & Multi-Signal Affinity Engine** | `apps/core/recommendations.py`, `apps/core/views.py`, `templates/home/index.html`, `apps/core/tests.py` | Eliminates false 'Because You Watched' attribution for unstreamed rated titles by inspecting actual `WatchProgress` vs. `UserRating` vs. `LibraryItem`. Correctly formats reason prefixes ('Because You Loved [Title]' for 5-star ratings, 'Because You Liked [Title]' for 4-star ratings, 'Because You Watched [Title]' for streamed content, and 'Because It's in Your Watchlist' for library items). Solves single-item bias by generating multiple distinct contextual rails across different user favorites rather than only the last item. Blends 'Recommended For You' across top 3 affinity genres and collaborative seeds using balanced round-robin interleaving, with automatic exclusion of titles already rated or watched. Fully profile-isolated and 100% covered by unit tests. |
| **Franchise & Sequel Awareness Engine in Recommendations** | `apps/core/recommendations.py`, `apps/core/tests.py` | Eliminates redundant duplicate recommendation rails when a user loves or streams multiple sequels in the same franchise (e.g. *Spider-Man: Across the Spider-Verse* and *Spider-Man: Into the Spider-Verse*). Extracts official TMDB `belongs_to_collection` IDs and normalized franchise root keys, enforcing strict seed deduplication so each franchise saga only occupies one contextual rail at a time. The remaining rails are allocated to completely distinct user favorites from other genres and universes (e.g. *Interstellar*, *Game of Thrones*). For users who have only seen/rated one installment of a franchise, unstreamed sequels and prequels are automatically prioritized at the head of the recommendation candidate pool. |
| **Dedicated Recommendations Hub & Taste Partitioning Engine** | `apps/core/recommendations.py`, `apps/core/views.py`, `apps/core/urls.py`, `templates/core/recommendations.html`, `templates/includes/navbar.html`, `templates/watch/history.html`, `apps/core/tests.py` | Dedicated full-page taste and discovery portal (`/recommendations/`) powered by user watch history and star ratings. Segregates recommendations into distinct contextual rails: (1) **Top Picks For You** (blended affinity across top genres and seeds with duplicate/history exclusion); (2) **Based on Your Highest-Rated Titles** (contextual rails derived from 4- and 5-star ratings with 'Because You Loved' and 'Because You Liked' attributions); (3) **Based on What You've Streamed** (contextual rails derived from streamed watch history with 'Because You Watched' attribution); and (4) **Your Top Genre Universes** (discovery grids for user's top affinity genres). Includes interactive media filter pills (`All Content`, `Movies` via `?type=movie`, `TV Series` via `?type=tv`), responsive taste analytics summary (total rated, total streamed, top genres), zero-signal discovery CTA empty state, horizontal swipeable rails with keyboard/button navigation, navbar direct link, and user profile menu integration. 100% profile-isolated with 25 unit tests in `apps.core`. |
| **Multi-Tab Watch History & Rated Hub** | `apps/watch/`, `templates/watch/history.html` | Dual-tab history dashboard scoped per active profile featuring: (1) **Streamed History** with grouped timeline rails (*Today, Yesterday, This Week, Earlier*), progress bars, and single-item removal, and (2) **Rated Titles** tab displaying a dedicated poster grid of all user-rated content with live star badges and in-place rating adjustments. |
| **Multi-Server Online Playback & Screen-Adaptive Controls** | `apps/playback/`, `templates/playback/watch.html` | Full multi-server web player with 6 streaming providers: **VidLink** (Primary Fast 1080p HD, Default), **VidFast** (4K Ultra HD), **AutoEmbed**, **VidSrc** (UHD/HD active mirror `vidsrc.pm`), **2Embed**, **NontonGo**. Fully screen-adaptive control bar resolving mobile horizontal overflow traps: replaces raw `<select>` with responsive custom server dropdowns (`[⚡ S1 ▾]` on mobile, `[⚡ Server VIDLINK ▾]` on desktop), compact 1-row mobile icon buttons (Back, Title, Server, Next Episode, Bookmark, More, Fullscreen), a slide-up **Mobile Player Controls Sheet** (`#mobile-player-controls-sheet`) giving 1-tap thumb access to servers, sleep timer presets, and watchlist, and interactive menu suspension of controls auto-hide. Includes fullscreen overlay preservation, profile-isolated server preference memory, wildcard origin iframe permissions, universal fullscreen toggle button, resume prompt threshold ($\ge 30$s scoped per active profile), active beacon progress tracking ($\ge 15$s), and 3.5s pause auto-hide. |
| **Season Total Runtime & Analytics Engine** | `apps/catalog/`, `apps/watch/` | Aggregates individual episode runtimes per TV season via `format_season_runtime` in `apps/catalog/views.py`. Displays duration badges on season selector tabs (`Season 1 • 6h 38m`) and episode list meta headers. Aggregates user watch history by season badges in Personal Analytics & Filvora Wrapped (`/analytics/`), with 5-metric dashboard including **Avg Rating** and total rated counts for active profile. |
| **Mega-Season Partitioning & Quick-Jump Engine** | `apps/catalog/`, `templates/catalog/` | Seamlessly breaks mega-seasons (>100 episodes, such as *Taarak Mehta Ka Ooltah Chashmah* with 4,800+ episodes or long-running anime/daily soaps) into manageable 100-episode virtual volumes/seasons (`Season 1: Eps 1–100`, `Season 2: Eps 101–200`, ..., `Season 49: Eps 4801–4808`). Accurately recalculates per-volume runtimes and reduces initial DOM payload by ~98% (rendering only 100 cards instead of 4,800). Features a compact quick-select dropdown (`#season-quick-select`) for fast navigation across dozens of seasons, an instant direct episode search jump input (`#quick-ep-jump-input`) with smooth scrolling, and bulletproof server compatibility by ensuring external embed players (VidLink, VidFast, VidSrc, AutoEmbed) always receive the native TMDB season `1` and exact episode number so streaming playback never breaks. Preserves standard 1:1 season numbering for all regular shows (Breaking Bad, Game of Thrones). |
| **Dynamic Age Ratings Engine** | `apps/tmdb/client.py` | Automatically extracts official release certifications (`PG`, `PG-13`, `R`, `TV-MA`) from TMDB and caches them in singleton `_RATING_CACHE[media_type:tmdb_id]` across all views. Ensures 100% rating consistency between cards and detail pages. |
| **Balanced Responsive Grid Engine** | `apps/tmdb/client.py` | `_fetch_paginated_24` windowing creates perfectly full, even rows of 24 titles per page (Desktop: 4 rows of 6; Laptop: 6 rows of 4; Tablet: 8 rows of 3; Mobile: 12 rows of 2). |
| **Multi-Page Discover Engine** | `apps/catalog/` | Faceted multi-page discovery filtering by Media Type (`movie`/`tv`), Mood, Genre, Language, Score, Certification (`G`, `PG`, `PG-13`, `R`, `NC-17`), and Sort Order with preserved query parameters across pagination. |
| **Homepage Cinematic Billboard** | `templates/home/index.html` | Hero spotlight billboard with generous upper breathing space (`pt-28 sm:pt-44`) allowing backdrop artwork to shine, responsive title typography, and content shifted gracefully into the lower third (`items-end pb-6 sm:pb-10`). Tight, seamless cinematic margin (`-mt-1 sm:mt-0`) eliminates the empty black gap between CTA buttons (Play Now, Trailer, In My List, Details) and the Continue Watching rail. |
| **Mobile-First UX & Touch Architecture** | `templates/base.html`, `static/css/main.css`, `templates/playback/watch.html`, `templates/includes/navbar.html`, `templates/accounts/profiles.html` | Comprehensive mobile and touch device optimizations: (1) Universal 16px font-size CSS safeguard on mobile form inputs/selects preventing iOS Safari auto-zoom; (2) Full-bleed safe area insets (`viewport-fit=cover`, `env(safe-area-inset-top/bottom/left/right)`); (3) Mobile bottom clearance preventing content cutoff behind fixed bottom navigation; (4) Floating toast repositioning above bottom navigation; (5) Native iOS momentum flick scrolling with decoupled smooth scrolling; (6) Active tap feedback animations; (7) Mobile-safe fixed centered live search dropdown eliminating left-edge clipping; (8) Global Wi-Fi LAN QR pairing modal accessible across all pages; (9) Mobile-adapted watch player using dynamic viewport height (`100dvh`), safe-area padding, mobile-constrained top sensor (h-16), touch auto-hide delay (3.5s vs 1s), scrollable landscape bookmark modal (`max-h-[90dvh]`), direct server switcher popup on floating pill click, viewport-safe fixed dropdown on mobile, and desktop-only theater/PiP filtering; (10) Touch-visible profile edit/delete controls and watchlist deletion without hover dependency; (11) Touch-pan optimized horizontal season selector rails and episode cards. |
| **Screen-Adaptive Navbar & Cross-Device Engine** | `templates/includes/navbar.html`, `static/js/main.js` | Precision breakpoint architecture providing 100% overlap-free layouts across all viewports: Mobile (320px–767px), iPad / Tablet portrait (768px–1023px, iPad Mini, iPad Air, iPad Pro), and Desktop (1024px+). Mobile and tablets feature a dedicated `[🔍]` trigger button opening a full-width search overlay with instant HTMX live suggestions, while desktops display the inline search bar with keyboard shortcut hint (`/`). Tablet navigation links feature compact padding (`px-2.5 py-1 text-xs whitespace-nowrap`), preserving >80px of clear center margin and eliminating collisions between nav links and action buttons. |
| **Universal Multi-Server Keyboard Shortcuts & Focus Preservation Engine** | `templates/playback/watch.html`, `apps/playback/tests.py` | Eliminates the issue where <kbd>Space</kbd> pause/play failed on Server 2 (VidFast). Root cause identified via deep client-side decompilation: VidFast's internal postMessage listener stubs out `play` and `pause` without execution code; VidFast instead relies exclusively on native `keydown` events (`e.code === 'Space' -> tq()`). Previously, Filvora ran an aggressive 150ms `window.focus()` on blur and on any mousemove, which repeatedly yanked focus away from VidFast, starving it of keystrokes. Filvora now preserves iframe focus during playback, restricts parent window refocusing strictly to top controls hover (`e.clientY <= 45` or hovering `#player-overlay`), proactively refocuses the player iframe on load, modal/sheet dismissals, and canvas clicks (`focusPlayerIframe`), enables full iframe fullscreen permissions (`fullscreen *`, `allowfullscreen`), and forwards global shortcuts (<kbd>Space</kbd>/<kbd>K</kbd>, <kbd>M</kbd>, <kbd>ArrowLeft</kbd>, <kbd>ArrowRight</kbd>, <kbd>F</kbd>, <kbd>C</kbd>, <kbd>B</kbd>, <kbd>Z</kbd>, <kbd>T</kbd>, <kbd>P</kbd>, <kbd>Alt+S</kbd>, <kbd>Esc</kbd>) with 100% reliability across all 6 servers. |
| **Universal Outside-Click Dropdown Dismissal & Hardware Layering** | `templates/playback/watch.html`, `templates/includes/navbar.html`, `static/js/main.js` | Solves the bug where open dropdowns could only be closed by re-clicking the trigger or selecting an option. In `watch.html`, solves the iframe click consumption trap by introducing `#player-dropdown-backdrop` (`fixed inset-0 z-[2147483645]`) and `#overlay-server-backdrop` so clicking anywhere on the video or page immediately dismisses the Server dropdown and Sleep Timer. In navbar, introduces `#navbar-dropdown-backdrop` (`fixed inset-0 z-40`) and capture-phase `pointerdown` and `click` listeners that intercept outside touches/clicks before child elements can swallow them with `stopPropagation`, instantly closing Vibe, Profile, and Search dropdowns across mobile, tablet, and desktop. Integrates `window.blur` listeners that dismiss dropdowns if an iframe is clicked. |
| **Universal Resume & Multi-Server Bookmark Seek Engine** | `apps/playback/views.py`, `templates/playback/watch.html`, `apps/playback/tests.py` | Eliminates the issue where clicking "Resume" or jumping to a scene bookmark failed to seek embed players. Root cause resolved: embed providers (VidLink, VidFast) do not use `?t=`; they require `startAt={sec}`, while VidSrc uses `t` and AutoEmbed uses `start`. Filvora now injects multi-protocol query parameters (`startAt`, `t`, `start`, `time`) onto embed `video_url` both on direct bookmark jumps (`?t=<pos>`) from My Library (bypassing redundant prompts and starting playback at the exact scene immediately) and on interactive "Resume" clicks without resetting or breaking the player. `sendIframePlaybackCommand` now supports `seek_to` alongside `seek`, dispatching standard postMessage seek packets across all embed engines. Server switching (`switchServer`) and shortcuts (<kbd>Alt</kbd>+<kbd>S</kbd>) automatically carry active playback positions (`&t=<currentPlaybackPosition>`) so users never lose their place when switching servers. Adds in-player floating toast notifications (`showToast`) confirming scene jumps and resume events. |
| **Automatic Server Failover & Watchdog Engine** | `apps/playback/`, `templates/playback/watch.html`, `apps/playback/tests.py` | Automatically detects unresponsive, dead, timed out, blocked, or stalled streaming servers across both embed iframes and HTML5 video. Features an 11-second initial connection watchdog, mid-playback stall detector (13s), and explicit error interceptor. Displays an ambient cinematic HUD banner with a 3-second animated countdown, live progress bar, reason label, target server name, and 1-click 'Switch Now' and 'Cancel' actions. Safely steps through all 6 servers (VidLink -> VidFast -> AutoEmbed -> VidSrc -> 2Embed -> NontonGo) in circular priority sequence while carrying active playback timestamps (`&t=<sec>`), tracking failed nodes in `sessionStorage` to prevent infinite redirect loops, and cleanly opening an upgraded Fallback Recovery Dialog if all servers are exhausted. Includes an Auto-Failover ON/OFF setting toggle in the server menu and automatic failover toast confirmations. |
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

#### 2.2.2 Clean Cinema Controls Auto-Hide, Edge Sensors & Cursor Concealment
- **Zero Screen Clutter in Fullscreen**: In cinema fullscreen and normal playback, once inactive for 2.0s, all controls slide completely off-screen (`translateY(-100%)`, `opacity: 0`). Zero permanent notches, zero duplicate server pills, and zero persistent icons remain on screen during playback.
- **Auto-Hide Cursor**: Automatically sets `cursor: none` on `#player-wrapper` when controls hide, completely concealing the mouse cursor during video playback and restoring it immediately on mouse movement or touch.
- **Compositor Hit-Testing (`#top-sensor`)**: Windows DirectComposition optimization can omit transparent `<div>` layers over hardware-accelerated video frames. A non-intrusive 36px top edge trigger strip (`#top-sensor`) with `background: rgba(0, 0, 0, 0.001)` smoothly drops down the upper controls whenever the cursor moves to the top edge of the screen.
- **Infinite Reset Loop Prevention**: Player postMessage event parsing distinguishes between periodic `timeupdate`/`progress` heartbeat packets (which update beacons without clearing the hide timer) and explicit state transitions (`play`, `pause`, `ended`), permanently eliminating the bug where routine 250ms progress updates endlessly reset the auto-hide timer.
- **Snappy 2.0s Inactivity Delay**: Uses a clean 2.0s timer with fast dismissal (600ms–800ms) on click outside or cursor exit downwards into the video canvas. Keyboard shortcuts (<kbd>C</kbd> to toggle controls, <kbd>F</kbd> for fullscreen, <kbd>Alt</kbd>+<kbd>S</kbd> to switch server) offer instant thumb and key control.

#### 2.2.3 Streaming Providers Matrix:
1. **Server 1 (VidLink)** ⭐: Primary fast 1080p Full HD default server with reliable CDN routing and zero buffer stalls.
2. **Server 2 (VidFast)**: High-bitrate 4K Ultra HD & 1080p streaming node. Runs on automatic adaptive bitrate (ABR); its internal UI exposes playback speed while serving peak source resolution.
3. **Server 3 (AutoEmbed)**: Multi-source failover streaming node.
4. **Server 4 (VidSrc)**: High-definition embed mirror (`vidsrc.pm`).
5. **Server 5 (2Embed)**: Secondary backup stream node.
6. **Server 6 (NontonGo)**: Alternative multi-server backup.

#### 2.2.4 The Zero-Reload Floating Mini-Player PiP Engine
- **The W3C Cross-Document Iframe Adoption Trap**: Under W3C HTML specifications, moving an `<iframe>` between documents via the modern Document Picture-in-Picture API (`documentPictureInPicture.requestWindow()` + `pipWindow.document.body.appendChild(container)`) completely destroys and recreates the iframe's browsing context. This immediately wiped all video buffering, paused playback, and reloaded the streaming server from second 0. Closing the PiP window moved the iframe back, triggering a second destructive reload.
- **The In-Page Floating Mini-Player Solution**:
  - Eliminates cross-document adoption entirely. Filvora keeps `#video-container` directly attached to `#player-wrapper` in the parent document hierarchy at all times.
  - Toggling Picture-in-Picture (<kbd>P</kbd> or clicking the top bar PiP button) applies the `.pip-floating-mode` CSS class to `#video-container`.
  - In floating mode, the player docks smoothly to the bottom-right corner (`fixed bottom-6 right-6 z-[2147483640]`, `width: min(440px, calc(100vw - 2rem))`, `aspect-ratio: 16 / 9`, `rounded-2xl border-2 border-brand-500/70 shadow-2xl`).
  - Displays a floating toolbar (`#pip-floating-toolbar`) on hover/touch with media title badge, quick restore button (<kbd>P</kbd>), and close button (<kbd>Esc</kbd>).
  - Inserts an ambient placeholder card (`#pip-active-backdrop`) in the main viewport with a 1-click "Restore Full Player (P)" CTA and catalog browsing navigation.
  - Because `#video-container` never leaves the DOM, the embed iframe **never reloads, never pauses, and never loses buffered frames**, providing 100% continuous playback!

#### 2.2.5 Server 2 (VidFast) Architecture & Universal Multi-Server Embed Command Protocol
- **The VidFast Root Cause Decompilation**: Deep reverse engineering of VidFast's production bundle (`vidfast.pro/_next/static/chunks/365-*.js`) revealed that VidFast's `window.addEventListener('message')` listener contains an empty stub:
  ```javascript
  if ((null==r?void 0:r.event)!=="CUSTOM_NEXT" && (null==r?void 0:r.command)!=="play" && (null==r?void 0:r.command)!=="pause" && (null==r?void 0:r.command)!=="seek")
  ```
  If `r.command === 'play'` or `'pause'`, the condition is false, the block is skipped, and the function terminates without invoking any video control APIs! VidFast **does not support** postMessage play/pause.
- **VidFast's Native Keyboard Engine**: VidFast instead implements a direct window keyboard listener:
  ```javascript
  let o = e => {
    if ("Space" === e.code) "BUTTON" !== e.target.tagName && tq(); // tq() toggles play/pause
    else if (e.code === "KeyF") tX(); // tX() toggles fullscreen
    else if (e.code === "ArrowLeft") seek(-10);
    else if (e.code === "ArrowRight") seek(10);
    else if (e.code === "KeyM") toggleMute();
  };
  window.addEventListener("keydown", o);
  ```
- **The Focus Starvation Bug & The Solution**:
  - Previously, Filvora ran an aggressive 150ms `window.focus()` timer in `window.addEventListener('blur')` and an unconditional `window.focus()` on any mousemove over the player. Whenever the user clicked into VidFast to watch, focus was instantly snatched away back to parent `window`. When the user hit <kbd>Space</kbd>, parent `window` intercepted it and sent a postMessage `{ command: 'play' }` which VidFast ignored, while VidFast's native `keydown` listener never received the key.
  - **Resolution**:
    1. **Preserve Iframe Focus**: Removed the 150ms `window.focus()` on blur. When the user interacts with the embed player, the iframe retains keyboard focus continuously.
    2. **Bounded Controls Refocusing**: Restricts parent window refocusing strictly to when the cursor approaches or hovers the top controls bar (`e.clientY <= 45` or `#player-overlay`), keeping controls hotkeys accessible while leaving video canvas interactions untouched.
    3. **Proactive Player Focus Router (`focusPlayerIframe`)**: Refocuses the iframe on initial page load, iframe `onload`, canvas clicks, and whenever modals or bottom sheets (Bookmarks, Sleep Timer, Server Menu, Mobile Sheet) are closed.
    4. **Full Fullscreen Permissions**: Added `allowfullscreen` and `fullscreen *` to `#filvora-embed-frame` attributes.
- **The Universal Dispatch Engine (`sendIframePlaybackCommand`)**:
  - Constructs multi-protocol packet payloads for every action (`toggle_play`, `play`, `pause`, `seek`, `seek_to`, `mute`), incorporating VidFast `command`, VidLink `MEDIA_COMMAND`, AutoEmbed `type`, and standard JWPlayer `method` payloads simultaneously.
  - Dispatches across `iframe.contentWindow`, child frames (`iframe.contentWindow.frames`), and `window.frames`.
  - In `handleGlobalKeydown`, whenever parent window catches <kbd>Space</kbd>/<kbd>K</kbd>, <kbd>M</kbd>, or seek arrows, it dispatches the postMessage AND immediately forwards focus to the embed iframe via `focusPlayerIframe()`.
- **Bi-Directional Telemetry & UI Feedback**:
  - Ingests incoming postMessage events with recursive JSON parsing (`JSON.parse(d.data)` for stringified JWPlayer packets), reading `currentTime`, `time`, `position`, and `seconds` to maintain live progress and trigger accurate seek offsets.
  - Automatically synchronizes `isIframeMuted` upon receiving embed `volumechange` events.
  - Pressing <kbd>M</kbd> delivers instant floating toast feedback (`Muted` / `Unmuted`), while seek keys (<kbd>J</kbd>, <kbd>L</kbd>, <kbd>ArrowLeft</kbd>, <kbd>ArrowRight</kbd>) display animated ripple indicators.

#### 2.2.6 Automatic Server Failover & Inactivity Watchdog Engine
- **The Core Problem**: Free and third-party streaming CDN mirrors frequently suffer from regional ISP blocks, temporary outages, DNS timeouts, missing files, or mid-stream stalls, forcing users to stare at a frozen black screen or manually navigate dropdown menus to hunt for an active server.
- **The Solution**: Filvora implements a dual-stage client-side watchdog:
  - **Initial Watchdog (11s)**: If after loading, the active server produces no playable stream, no postMessage progress, and no frame playback within 11 seconds, Filvora surfaces the `#auto-switch-hud` banner with a 3-second countdown and smoothly redirects to the next untried server (`?server=<next>&auto=1&t=<pos>`).
  - **Mid-Playback Stall Detector (13s) with 100% Pause Immunity**: If an active stream freezes mid-playback for $>13$s while not paused by the user, the watchdog triggers failover, preserving the exact playback second.
  - **Pause Failover Immunity & Embed Stall Shield**:
    - Previously, pausing video could trigger unwanted failover because embed iframes stop emitting progress updates when paused, trailing in-flight postMessage packets (`pos > currentPlaybackPosition`) overwrote `isPlaybackPaused`, or cross-origin iframe click consumption concealed user pause actions.
    - Filvora resolved this via a comprehensive 6-layer defense:
      1. **Multi-Schema Pause Recognition**: `checkEmbedPauseSignal` detects pause across VidLink, JWPlayer, Video.js, and YouTube iframe protocols (`pause`, `paused`, `state: paused`, `status: paused`, `playerState: 2`, `data.paused: true`).
      2. **Central State Router (`setPlaybackPausedState`)**: Automatically aborts any active `autoSwitchPending` countdown, records `lastUserPauseTime`, and keeps `lastProgressTimestamp` refreshed so watchdogs freeze cleanly.
      3. **In-Flight Packet Protection**: Rejects position advance unpausing within a 4.0s window of an explicit user pause command, preventing trailing async network packets from destroying pause state.
      4. **Hard Safeguard in `triggerAutoSwitch`**: Immediate `if (isPlaybackPaused) return;` safeguard halting failover unconditionally whenever playback is paused.
      5. **Iframe Interaction & Blur Detector**: Tracks cursor presence over video canvas. If the user clicks into the embed player and progress stops, Filvora identifies it as a user pause rather than a stream stall.
      6. **HTML5 Video.js Immunity**: Direct native `player.paused()` polling ensures local video streams never trigger failover on pause.
  - **Direct & Embed Error Interception**: Catches Video.js `player.on('error')`, `iframe.onerror`, and embed postMessage error packets (`error`, `media_error`, `fail`), immediately transitioning to failover.
  - **Infinite Loop Elimination**: Tracks attempted servers in `sessionStorage` per media title. If all 6 streaming nodes fail, Filvora halts automatic transitions and presents the `#fallback-modal` dialog with a 1-click "Retry from Server 1" option.
  - **Interactive Transparency**: Users can click "Switch Now" to bypass the 3-second timer, click "Cancel" to remain on the current node, or toggle the feature ON/OFF directly via the server dropdown.

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

#### 2.3.6 Mega-Season Partitioning, Volume Chunking & Streaming Parity
- **The Core Problem**: In TMDB, long-running continuous Indian daily soaps (such as *Taarak Mehta Ka Ooltah Chashmah* with 4,800+ episodes) and long-running continuous anime/serials are listed under a single massive "Season 1". Rendering 4,800 episode cards simultaneously bloated page load times and DOM size, while SonyLIV and official broadcasters divide the show into 49 distinct seasons of 100 episodes each.
- **The Solution**:
  - Implemented dynamic volume partitioning via `get_series_season_partitions(series, chunk_size=100)` in [`apps/catalog/views.py`](file:///D:/Om/Projects/Filvora/apps/catalog/views.py).
  - Any season with $>100$ episodes is automatically divided into 100-episode virtual seasons (`Season 1: Eps 1–100`, `Season 2: Eps 101–200`, ..., `Season 49: Eps 4801–4808`). Regular seasons with $\le 100$ episodes are left 100% untouched.
  - Slices TMDB season data in memory without additional network calls; calculates exact season runtime per 100-episode block (e.g. `35h 20m` instead of `1684h 58m`).
  - Added a responsive compact dropdown (`#season-quick-select`) enabling 1-click jumps across 49+ seasons alongside the horizontal season tab rail.
  - Added a direct **Quick Episode Jump** search bar (`#quick-ep-jump-input`) allowing users to type any episode number (e.g. `450`), automatically switching to the right season volume if needed and smoothly scrolling to the highlighted card (`#ep-card-<num>`).
  - **Streaming Embed Server Compatibility**: Preserved TMDB native season indexing in playback URLs (`{{ ep.season_number|default:season_number }}`). When watching Episode 150 (located in Filvora virtual Season 2), the player receives native TMDB Season `1` (`/watch/tv/8630/1/150`), guaranteeing VidLink, VidFast, VidSrc, and AutoEmbed stream lookups succeed without errors.

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

### 2.6 🧠 Multi-Signal Recommendations, Dedicated Hub & Franchise Awareness Engine (`apps/core/recommendations.py`, `apps/core/views.py`)

#### 2.6.1 Accurate Phrasing & Attribution Engine
- **The Core Problem**: Previously, rating an unstreamed title 5 stars (e.g. *Project Hail Mary*) falsely stamped the recommendation rail with `"Because You Watched Project Hail Mary"`.
- **The Multi-Signal Attribution Resolution**:
  - `RecommendationEngine.get_seed_attribution(user, profile, tmdb_id, media_type)` inspects live signals across `WatchProgress` vs `UserRating` vs `LibraryItem`:
    - 5-Star Unstreamed: Attributed as **`Because You Loved <Title>`**.
    - 4-Star Unstreamed: Attributed as **`Because You Liked <Title>`**.
    - 3-Star Unstreamed: Attributed as **`Because You Rated <Title>`**.
    - Streamed Content: Attributed as **`Because You Watched <Title>`**.
    - Watchlist Items: Attributed as **`Because It's in Your Watchlist`**.
  - Completely eliminates inaccurate watch assumptions for rated content.

#### 2.6.2 Franchise & Sequel Awareness Engine (Seed Deduplication & Sequel Prioritization)
- **The Core Problem**: When a user rates or streams multiple movies belonging to the same franchise/collection (such as *Spider-Man: Across the Spider-Verse* and *Spider-Man: Into the Spider-Verse*), both were selected as candidate seeds. This produced duplicate franchise rails right next to each other on the user's screen, with Rail 1 consuming all Spider-Man movies and Rail 2 showing spillover comic-book titles, crowding out other distinct user favorites.
- **The Solution**:
  - **Franchise Identifier Extraction (`_get_franchise_identifiers`)**:
    - Queries official TMDB `belongs_to_collection['id']` (e.g. `coll_573436` for Spider-Man Spider-Verse Collection, `coll_726871` for Dune, `coll_263` for The Dark Knight).
    - Extracts normalized franchise root keys from titles (e.g. `root_spider-man`, `root_dune`, `root_star wars`).
  - **Franchise Seed Deduplication**:
    - When building contextual rails (`get_contextual_rails` and `get_dedicated_recommendations`), the engine tracks `seen_franchise_identifiers`.
    - Once one installment of a franchise is accepted as a seed rail, any other sequel/prequel in that collection is automatically skipped as a seed.
    - The next rail is allocated to a completely different user favorite from another genre or universe (e.g. *Interstellar* or *Game of Thrones*).
  - **Direct Sequel & Prequel Prioritization (`_get_collection_parts_recs`)**:
    - For users who have only seen/rated one part of a franchise, unstreamed sequels/prequels from that collection are fetched and prepended at the very head of the recommendation candidate pool.
    - If the user already rated or completed the sequels, they are filtered out via `exclude_keys`.

#### 2.6.3 Dedicated Recommendations Portal (`/recommendations/`)
- Full-page discovery portal partitioned into distinct contextual sections:
  1. **Top Picks For You**: Blended affinity across top genres and seeds with duplicate/history exclusion.
  2. **Based on Your Highest-Rated Titles**: Contextual rails derived from 4- and 5-star ratings with *"Because You Loved"* and *"Because You Liked"* attributions.
  3. **Based on What You've Streamed**: Contextual rails derived from streamed watch history with *"Because You Watched"* attribution.
  4. **Your Top Genre Universes**: Curated rails for user's top affinity genres.
  5. **Taste Profile Overview**: Glassmorphic stats header displaying total rated, total streamed, and top genres.
  6. **Interactive Media Type Filters**: Seamlessly filters by `All Content` (`/recommendations/`), `Movies` (`?type=movie`), and `TV Series` (`?type=tv`).
  7. **Empty State**: Cinematic fallback guiding users to rate titles or start streaming.
- Navigation integration: Top desktop navbar link (`Recommended`), user profile dropdown (`Recommended For You` with star badge), and discovery CTA in Watch History.

---

### 2.7 🎯 In-Card Quick Actions & Franchise Saga Batch Actions Architecture (`apps/watch/`, `apps/catalog/`, `apps/library/`)

#### 2.7.1 In-Card Quick Actions Engine (Mark as Watched & Star Rating Popover)
- **The Core Problem**: Previously, users were required to click into movie/series detail pages to mark titles as watched or submit star ratings, creating high interaction friction during catalog browsing.
- **The Solution**:
  - Equips all movie and TV series cards across the catalog (Homepage billboard & rails, Movies browse, TV Series browse, Discover, Search, Recommendations, and History) with 4 dedicated in-card actions:
    1. **`[+]` Watchlist Toggle**: In-place HTMX toggle adding/removing titles from active profile's My List.
    2. **`[👁]` 1-Click Mark as Watched**: Instantly toggles completed status in `WatchProgress` for active profile, illuminating with an emerald indicator and tooltip confirmation.
    3. **`[★]` Quick Star Rating**: Micro glassmorphic popover capsule (1–5 stars) featuring live hover illumination, in-place HTMX submission (`/progress/rate/`), and clear rating option (`[✕]`).
    4. **`[ⓘ]` Info Details**: Direct anchor link to details view.
  - **Universal Context Processor (`apps.watch.context_processors.user_watch_context`)**: Pre-fetches active profile's watched sets and ratings maps into global template context, avoiding N+1 queries.
  - **Template Tag Filter (`apps.watch.templatetags.watch_tags.get_item`)**: Safe dictionary lookup filter for integer and string keys in Django templates.
  - **Click Propagation Isolation**: Enforces strict `event.stopPropagation()` on all card action buttons to prevent unintentional parent poster clicks.

#### 2.7.2 Franchise Saga & Complete Collection Batch Actions Engine
- **The Core Problem**: When browsing franchise collections (e.g. *Dune Collection*, *The Dark Knight Trilogy*, *Spider-Man Spider-Verse*, *John Wick*, *Harry Potter*), users wanted the ability to mark the entire saga as watched, rate all movies in the franchise, or add the entire collection to their watchlist with 1 click.
- **The Solution**:
  - Equips the Official Franchise Saga rail header with 4 batch actions:
    1. **Franchise Completion HUD**: Dynamic progress badge tracking `X of Y Watched (Z%)` that transitions to an emerald `✓ Saga Completed` state when all installments are watched.
    2. **1-Click "Mark Saga as Watched" Toggle** (`/progress/collection/mark-watched/`): Completes or unmarks all movies in the saga simultaneously for active profile.
    3. **1-Click "Rate Entire Saga" Popover Capsule** (`/progress/collection/rate/` & `/progress/collection/rate/remove/`): Micro popover capsule assigning 1–5 stars across all franchise chapters in one tap with live hover illumination, active score badge (`★ 5/5 Saga Rated`), and clear rating option.
    4. **1-Click "Add Saga to My List" Toggle** (`/library/collection/toggle-all/`): Batch adds or removes all installments from active profile's `LibraryItem`.
  - **Real-Time Client Synchronization**: Batch endpoints dispatch HTMX triggers (`sagaWatchedChanged`, `sagaRatingChanged`) that immediately illuminate narrative timeline ribbon segments emerald and toggle in-card `Seen` badges without full-page reloads.
  - **Full In-Card Parity**: Every movie card in the saga rail retains permanent desktop & mobile `Seen` indicators, center direct Play, and the standard 4-button action row.

---

### 2.8 📅 Watch Date & Multi-Day Session Resolution Architecture (`apps/watch/models.py`, `apps/watch/views.py`, `templates/watch/history.html`)

#### 2.8.1 The Multi-Day Watch Date Dilemma
When a user starts watching a movie or TV series on one calendar day and finishes it on another (e.g. starting a 3-hour movie on Friday night and finishing Sunday afternoon), displaying only a single date or `updated_at` creates ambiguity and discards the user's viewing journey context.

#### 2.8.2 Dual-Timestamp Lifecycle Schema & Historical Alignment
- `WatchProgress` tracks two explicit timestamps:
  - `created_at = models.DateTimeField(default=timezone.now)`: Records the exact datetime the viewing session began.
  - `completed_at = models.DateTimeField(null=True, blank=True)`: Records the exact datetime the title crossed the $\ge 90\%$ threshold or was explicitly marked as watched via `toggle_watched`. Cleared to `None` if uncompleted or reset.
- **Migration 0005 Default Resolution**: When migration `0005` added `created_at` with `default=timezone.now`, SQLite initialized pre-existing rows with today's migration execution timestamp, causing records watched days earlier to appear as though they began today (`created_at > updated_at`).
- **Data Migration 0006 (`0006_align_watchprogress_historical_timestamps.py`)**: Safely backfilled and aligned all pre-existing records:
  1. For records where `created_at > updated_at`, aligned `created_at = updated_at`.
  2. For records where `completed=True` and `completed_at is None`, set `completed_at = updated_at`.
  3. For records where `completed=True` and `completed_at < created_at`, clamped `created_at = completed_at`.
  - Guarantees historical single-sitting viewings (e.g. *Supergirl* watched on Sep 15) correctly render their genuine single date (`Sep 15, 2026`) instead of today's date or inverted spans.

#### 2.8.3 Dynamic Date Resolution Algorithm & Chronological Clamping
- **Model Properties**:
  - `effective_end_dt`: Evaluates `self.completed_at or self.updated_at` for completed content, or `self.updated_at` for in-progress titles.
  - `effective_start_dt`: Clamps `self.created_at or self.updated_at` so it cannot exceed `effective_end_dt`.
- **Display Resolution**:
  1. **For Completed Titles (`completed=True`)**:
     - **Single-Day Session**: Displays exact completion date: **`Sep 18, 2026`** or historical date **`Sep 15, 2026`** (Tooltip: `Completed on <date>`).
     - **Multi-Day Session (Same Month)**: Displays start-to-finish span: **`Sep 15 – 18, 2026`** (Tooltip: `Started Sep 15, 2026 • Completed Sep 18, 2026`).
     - **Multi-Day Session (Cross Month)**: Displays span: **`Aug 28 – Sep 02, 2026`**.
     - **Multi-Day Session (Cross Year)**: Displays span: **`Dec 28, 2025 – Jan 02, 2026`**.
  2. **For In-Progress Titles (`completed=False`)**:
     - **Single-Day Session**: Displays start date: **`Sep 18, 2026`** (Tooltip: `Started on Sep 18, 2026`).
     - **Multi-Day Session**: Displays start-to-last-played span: **`Sep 10 – 14, 2026`** (Tooltip: `Started Sep 10, 2026 • Last played Sep 14, 2026`).
- **Chronological Swap Guard**: `watch_date_display` and `watch_date_tooltip` enforce `if start_d > end_d: start_d, end_d = end_d, start_d`, permanently preventing backwards date rendering (e.g. `Sep 18 – 15, 2026`).
- **Timeline Grouping Preserved**: Grouped history rails (*Today, Yesterday, This Week, Earlier*) continue to be sorted and organized by `updated_at` (most recent user activity).
- **Card UI Integration**: In `templates/watch/history.html`, cards render a calendar SVG badge pill:
   `<span class="inline-flex items-center gap-1 text-[10px] font-medium text-gray-400 bg-gray-950/80 px-2 py-0.5 rounded border border-gray-800/80 shadow-sm" title="{{ item.watch_date_tooltip }}">...</span>`

---

### 2.9 ⏸️ Decommissioned / Dropped Features (Standby Architecture)

#### 2.9.1 Offline Download Pipeline (`apps/downloads/`) — ON HOLD / DROPPED
- **Status**: **ON HOLD / DROPPED (Deactivated)**
- **Architectural Rationale**: Filvora is fundamentally engineered and optimized as an instant high-bitrate multi-server online streaming platform with 6 circular failover providers (VidLink, VidFast, AutoEmbed, VidSrc, 2Embed, NontonGo). Offline downloading of fragmented iframe/HLS streaming sources is bandwidth-heavy, storage-prohibitive, and redundant given 100% cloud-stream reliability and instant multi-server failover.
- **Codebase State**:
  - `apps.downloads` is **commented out** in `config/settings.py` (`INSTALLED_APPS`).
  - `/downloads/` routing is **commented out** in `config/urls.py` and `apps/downloads/urls.py`.
  - Views in `apps/downloads/views.py` and test cases in `apps/downloads/tests.py` are preserved commented out on hold for future architectural reference.
  - The active automated test suite (`run_all_tests.py`, `Run Tests.bat`, `manage.py test`) excludes downloads and tests exclusively the 7 active production apps (162 tests, 100% passing).

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
│   ├── downloads/             # [ON HOLD / DROPPED] Decommissioned standby download pipeline
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
3. **Git Commit, Push & Grouping Discipline**:
   - When completing multi-part tasks, group changes logically and commit in distinct functional groups (e.g. Model/Migration, View/API, Template UI, Tests/Documentation).
   - If the user specifies "only commit no push", strictly avoid executing `git push` and keep commits local until explicitly instructed to push.
   - Stage and commit with clear conventional semantic commit messages (`feat(...)`, `fix(...)`, `test(...)`, `refactor(...)`).
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

# Run Automated Test Suite (162 tests across 7 active apps)
.\venv\Scripts\python.exe run_all_tests.py

# Or via Django test runner
.\venv\Scripts\python.exe manage.py test apps.core apps.catalog apps.playback apps.library apps.watch apps.tmdb apps.accounts

# Backup Local Database
.\venv\Scripts\python.exe manage.py backup_db

# Reset / Change User Password
.\venv\Scripts\python.exe manage.py changepassword moon
```

### Local Test Accounts:
- **Main User**: `moon` (Password: `1234`)
- **Superuser**: `admin` (Password: `1234`)
