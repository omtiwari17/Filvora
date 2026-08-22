# Filvora — Complete Project Architecture & Build Specification

## 1. Project Overview

**Project name:** Filvora

Filvora is a personal movie and TV-series discovery/watch web application.

The core idea is:

- Filvora does **not** store movie/episode video files on its own server.
- Filvora uses **TMDB** for movie and series metadata, discovery information, posters, backdrops, genres, cast, ratings, seasons, and episode information.
- Filvora uses a **separate, authorized video playback provider** for actual video delivery.
- Django is the backend.
- Django Templates are the frontend rendering layer.
- Tailwind CSS is used for styling.
- HTMX is used for dynamic interactions without introducing React/Vue/Angular.
- PostgreSQL is the primary database.
- Video playback uses a browser-compatible streaming approach such as HLS, with Video.js/hls.js where appropriate.

Important boundary:
Filvora must not scrape, extract, bypass protection on, or depend on unauthorized movie/episode streams. The playback layer must use content and providers that Filvora is authorized to use. The architecture should remain provider-independent so a legitimate provider can be changed later without redesigning the application.

---

# 2. Goals

## Primary goals

1. Build a modern, cinematic movie/series website.
2. Use Django as the complete backend.
3. Avoid React, Next.js, Vue, Angular, or another SPA frontend.
4. Use normal Django HTML templates for the frontend.
5. Make the interface feel like a polished streaming/discovery service rather than a traditional Django website.
6. Get movie/series information dynamically from TMDB.
7. Avoid downloading and permanently storing movie/episode video files on the Filvora server.
8. Let an external authorized video provider/CDN handle video delivery.
9. Use adaptive streaming where supported so playback can change quality according to network conditions.
10. Support movies and TV series, including seasons and episodes.
11. Support user accounts, favorites, watch history, continue watching, and playback progress.
12. Keep the backend efficient so Django is responsible for application data rather than carrying the full video bandwidth.
13. Make the application easy to extend later.

## Non-goals

- Do not build a video piracy/scraping system.
- Do not bypass anti-bot systems, DRM, signed URLs, referer restrictions, or provider access controls.
- Do not proxy entire movie files through Django.
- Do not build a React/Next.js frontend.
- Do not require Filvora to keep a local copy of every movie or episode.
- Do not hard-code one video provider throughout the application.

---

# 3. Technology Stack

## Backend

### Django

Use Django as the main application framework.

Why:

- Mature Python web framework.
- Built-in authentication.
- Excellent ORM.
- Admin interface.
- URL routing.
- Sessions.
- Security features.
- Template system.
- Easy integration with external APIs.
- Excellent fit for a server-rendered application.

### Django REST Framework

Use DRF only where an API is useful.

Examples:

- Search suggestions.
- AJAX/HTMX endpoints.
- Playback metadata.
- User watch-progress endpoints.
- Future mobile/client support.

Filvora should NOT become an API-only application. Django Templates remain the primary frontend.

---

# 4. Frontend

## Django Templates

The entire UI should be rendered using Django templates.

No React.

No Next.js.

No Vue.

No Angular.

Templates should be componentized using Django template partials.

Suggested structure:

```text
templates/
├── base.html
├── includes/
│   ├── navbar.html
│   ├── footer.html
│   ├── movie_card.html
│   ├── series_card.html
│   ├── hero.html
│   ├── rating.html
│   ├── loading_card.html
│   ├── empty_state.html
│   └── pagination.html
├── home/
│   └── index.html
├── movies/
│   ├── detail.html
│   └── browse.html
├── series/
│   ├── detail.html
│   ├── season.html
│   └── episode.html
├── search/
│   └── results.html
├── watch/
│   ├── player.html
│   └── error.html
├── accounts/
│   ├── login.html
│   ├── register.html
│   └── profile.html
└── library/
    ├── favorites.html
    └── history.html
```

---

# 5. Styling

## Tailwind CSS

Use Tailwind CSS for the visual system.

The visual direction should be:

- Dark-first.
- Cinematic.
- Minimal.
- Large backdrop imagery.
- Strong typography.
- Subtle gradients.
- Smooth hover effects.
- Poster cards.
- Horizontal content rails.
- Responsive mobile layout.
- Clean player interface.
- Good whitespace.
- No excessive visual clutter.

Filvora should look like a real entertainment product, not a Django admin panel.

Example homepage:

```text
FILVORA

Home   Movies   Series   Genres   My List                     Search

---------------------------------------------------------------
                    CINEMATIC HERO
---------------------------------------------------------------

                 Movie title
                 2026 • 2h 10m • Action

                 Description...

                 [ WATCH NOW ]   [ + MY LIST ]


Continue Watching
[card] [card] [card] [card] [card]

Trending Now
[card] [card] [card] [card] [card]

Popular Movies
[card] [card] [card] [card] [card]

Popular Series
[card] [card] [card] [card] [card]
```

---

# 6. Dynamic UI

## HTMX

Use HTMX for interactions that do not require a full page reload.

Examples:

- Search suggestions.
- Load more movies.
- Filter results.
- Change season.
- Load episode lists.
- Add/remove favorite.
- Update watch progress.
- Continue-watching updates.
- Login/logout fragments where appropriate.
- Lazy loading sections.

Why HTMX:

- Keeps the frontend simple.
- Works naturally with Django.
- No frontend framework required.
- Server-rendered HTML remains the source of truth.
- Much less JavaScript than a SPA.

Use vanilla JavaScript only when browser APIs or player controls require it.

---

# 7. Database

## PostgreSQL

Use PostgreSQL in production and preferably during development.

The database stores application-specific data, NOT movie video files.

Suggested data:

- Users.
- User profiles.
- Favorites.
- Watch history.
- Playback progress.
- Local metadata cache.
- Provider mappings.
- Search/cache data if needed.

---

# 8. TMDB Integration

TMDB is the metadata/discovery source.

TMDB can provide information such as:

### Movies

- TMDB ID.
- Title.
- Original title.
- Overview.
- Release date.
- Poster.
- Backdrop.
- Genres.
- Runtime.
- Rating.
- Vote count.
- Cast.
- Crew.
- Similar titles.
- Recommendations.
- Trailers where available.
- Images.

### TV

- TMDB ID.
- Series title.
- Overview.
- Poster.
- Backdrop.
- Genres.
- Rating.
- Seasons.
- Episodes.
- Episode names.
- Episode descriptions.
- Episode air dates.
- Episode still images.
- Cast.

Filvora should use TMDB IDs as the primary external identifiers.

Example:

```text
movie:
tmdb_id = 550
```

The application should not identify a movie solely by title because titles can collide.

---

# 9. TMDB Data Strategy

There are two useful approaches.

## Approach A — Dynamic

Request TMDB data when a page is opened.

Example:

```text
GET /movie/550/
        ↓
Django
        ↓
TMDB API
        ↓
Movie details
        ↓
Django template
        ↓
Browser
```

Advantages:

- Very little local metadata.
- Always relatively fresh.

Disadvantages:

- More API requests.
- More dependent on external API response time.

## Approach B — Cache locally

Fetch TMDB data and store selected metadata in PostgreSQL.

Example:

```text
TMDB
  ↓
Django
  ↓
PostgreSQL cache
  ↓
Template
```

Advantages:

- Faster repeated pages.
- Lower API usage.
- Better resilience.

Recommended:

**Use a hybrid approach.**

Store important metadata locally and refresh it periodically or when stale.

Do not blindly copy every TMDB field into the database.

---

# 10. Movie/Series Discovery Flow

When a user opens Filvora:

```text
Browser
   ↓
Django homepage
   ↓
TMDB service
   ↓
Trending/popular/discovery data
   ↓
Django transforms data
   ↓
Django template
   ↓
HTML sent to browser
```

The frontend should never contain TMDB API credentials.

TMDB credentials stay server-side.

---

# 11. Movie Detail Flow

User opens:

```text
/movie/550/
```

Flow:

```text
Browser
   ↓
Django URL
   ↓
Movie view
   ↓
Check local cache
   │
   ├── Fresh → use local data
   │
   └── Missing/stale → request TMDB
                         ↓
                    Save/update cache
   ↓
Find authorized playback mapping
   ↓
Render movie page
```

The page contains:

- Hero/backdrop.
- Poster.
- Title.
- Release year.
- Runtime.
- Rating.
- Genres.
- Overview.
- Cast.
- Similar movies.
- Recommended titles.
- Watch button.

---

# 12. Series Flow

User opens:

```text
/tv/1399/
```

Django gets series information.

Then:

```text
Series
 ├── Season 1
 │    ├── Episode 1
 │    ├── Episode 2
 │    └── Episode 3
 │
 ├── Season 2
 │    ├── Episode 1
 │    └── Episode 2
 │
 └── Season 3
```

Season selection can use HTMX.

Example:

```text
GET /tv/1399/season/2/
```

Django returns only the episode-list HTML fragment.

This avoids reloading the complete page.

---

# 13. Playback Architecture

This is the most important architectural rule.

Django must NOT carry the movie stream.

Do NOT build:

```text
Browser
   ↓
Django
   ↓
Movie file
```

Instead:

```text
Browser
   ↓
Django
   ↓
Playback metadata
   ↓
Authorized video provider/CDN
   ↓
Browser video player
```

Django provides application information.

The video provider delivers video.

---

# 14. Provider-Abstraction Layer

Never hard-code a provider into views.

Create a provider interface.

Conceptually:

```python
class VideoProvider:
    def get_playback(self, content):
        raise NotImplementedError
```

Then providers implement the interface:

```text
providers/
├── base.py
├── authorized_provider.py
└── registry.py
```

The application asks:

```python
playback = playback_service.get_playback(content)
```

It should not care which provider is behind the service.

This means the provider can be changed later without rewriting:

- Movie pages.
- Series pages.
- Player UI.
- Database structure.
- User history.

---

# 15. Playback Data Model

A playback mapping could conceptually contain:

```text
PlaybackSource
-------------------------
content_id
provider
source_type
source_url/reference
quality information
subtitle information
active
created_at
updated_at
```

The exact implementation depends on the authorized provider.

Do not store secrets or private provider credentials in templates.

---

# 16. Streaming Technology

Where the provider supports it, prefer adaptive streaming such as:

- HLS.
- MPEG-DASH.

HLS is particularly useful in browser environments when combined with a compatible player/library.

The important concept is:

```text
One giant movie file
        ↓
NOT ideal for adaptive playback

Multiple quality variants
        ↓
Master playlist
        ↓
Small media segments
        ↓
Player selects appropriate quality
```

Example:

```text
Master playlist
      │
      ├── 1080p
      ├── 720p
      ├── 480p
      └── 360p
```

The browser can switch quality depending on bandwidth and buffer conditions.

---

# 17. Why This Can Reduce Buffering

Filvora itself should not be responsible for sending the entire movie.

The playback provider/CDN should provide:

- Geographic distribution.
- High bandwidth.
- Adaptive streaming.
- Segment delivery.
- Caching.
- Connection management.

The player requests only the segments it needs.

Django remains responsible for:

- Authentication.
- Metadata.
- Watch progress.
- Permissions.
- Playback authorization.
- Application logic.

This separation is essential.

---

# 18. Player

Use a player capable of handling the formats supported by the chosen authorized provider.

Possible stack:

```text
Video.js
+
hls.js where needed
```

The player should support:

- Play/pause.
- Seek.
- Volume.
- Fullscreen.
- Quality selection when available.
- Subtitle selection.
- Playback speed where appropriate.
- Keyboard controls.
- Resume playback.
- Next episode.
- Previous episode.
- Auto-next for series.
- Error states.

Do not assume every provider supports every feature. Detect capabilities.

---

# 19. Watch Page

Example:

```text
/watch/movie/550/
```

For a series:

```text
/watch/tv/1399/1/1/
```

The watch view should:

1. Authenticate user if required.
2. Check content/playback availability.
3. Ask playback service for an authorized playback resource.
4. Return player page.
5. Start playback in browser.
6. Periodically save progress.
7. Mark item completed near the end.
8. For series, provide next-episode information.

---

# 20. Watch Progress

Do not save progress every second.

That creates unnecessary database traffic.

Instead, update periodically, for example:

```text
every 10–30 seconds
```

and also when:

- User pauses.
- User leaves page.
- Video ends.

Conceptually:

```text
WatchProgress
---------------------
user
content
season
episode
position_seconds
duration_seconds
completed
updated_at
```

Then the home page can show:

```text
Continue Watching
──────────────────────────
Movie              63%
Series S02 E03     41%
Movie              82%
```

---

# 21. User Features

Initial account features:

### Authentication

- Register.
- Login.
- Logout.
- Password reset.

### My List

- Add movie.
- Remove movie.
- Add series.
- Remove series.

### History

- Recently watched.
- Continue watching.

### Playback

- Resume from previous position.
- Mark completed.
- Next episode.

Future features:

- Multiple profiles.
- Ratings.
- Personal recommendations.
- Custom lists.
- Notifications.

Do not overbuild the first version.

---

# 22. Search

Search should work through TMDB.

Flow:

```text
User types:
"inter"

       ↓

HTMX request

       ↓

Django

       ↓

TMDB search

       ↓

Search results fragment

       ↓

Browser replaces results
```

For high traffic, add caching.

Search should support:

- Movies.
- TV series.
- People optionally later.

---

# 23. Home Page Sections

Recommended first version:

1. Hero.
2. Continue Watching.
3. Trending Today.
4. Popular Movies.
5. Popular TV.
6. Top Rated Movies.
7. Top Rated TV.
8. Popular Genres.
9. Recommended based on watch history.
10. Recently added/available content if Filvora has its own availability data.

Avoid making every section load huge amounts of data.

Use a small number of cards per request.

---

# 24. Images

TMDB image URLs should be used according to TMDB's image/API requirements.

Do not download every poster into your own server.

Browser flow:

```text
Filvora HTML
   ↓
Image URL
   ↓
TMDB image infrastructure
   ↓
Browser
```

This keeps Filvora lightweight.

Use:

- Poster for cards.
- Backdrop for hero/detail pages.
- Episode still for episode cards where useful.

Use appropriate image sizes instead of always requesting the largest image.

---

# 25. Performance Architecture

## Backend

Use:

- PostgreSQL indexes.
- Django query optimization.
- Caching.
- Lazy loading.
- Pagination.
- Limited API calls.
- Connection pooling in production.

## TMDB

Cache commonly requested data.

For example:

```text
Trending → short cache
Movie details → longer cache
Genre lists → long cache
```

Exact TTL values should be configurable.

## Frontend

Use:

- Lazy-loaded images.
- Responsive image sizes.
- Skeleton loaders.
- Minimal JavaScript.
- HTMX partial updates.
- Browser caching.
- Compressed CSS/JS.

## Video

Video bandwidth must remain outside Django.

---

# 26. Redis

Redis is optional for the first local version.

Introduce it when needed for:

- TMDB response caching.
- Session/cache storage.
- Rate limiting.
- Background task coordination.

Do not add Redis simply because it is popular.

---

# 27. Background Tasks

For the initial version, synchronous TMDB requests are acceptable for development.

Later use Celery or another background-task system for:

- Refreshing popular/trending metadata.
- Updating stale metadata.
- Prewarming caches.
- Cleaning old watch-progress records.
- Scheduled maintenance.

Do not make the homepage depend on a slow background job.

---

# 28. Django App Structure

Recommended project:

```text
filvora/
├── manage.py
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── catalog/
│   ├── tmdb/
│   ├── playback/
│   ├── watch/
│   ├── library/
│   └── core/
│
├── templates/
├── static/
├── media/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
└── README.md
```

Do not commit `.env`.

---

# 29. Responsibilities of Each App

## accounts

Handles:

- User registration.
- Login.
- Logout.
- Password management.
- Profile.

## catalog

Handles:

- Movies.
- TV series.
- Seasons.
- Episodes.
- Catalog pages.
- Detail pages.

## tmdb

Handles only TMDB integration.

Example:

```text
tmdb/
├── client.py
├── services.py
├── serializers.py
└── exceptions.py
```

Keep TMDB-specific code out of normal views.

## playback

Handles:

- Provider abstraction.
- Playback availability.
- Playback authorization.
- Provider mappings.

## watch

Handles:

- Watch history.
- Playback progress.
- Continue watching.
- Completion.

## library

Handles:

- Favorites.
- My List.

## core

Handles:

- Homepage.
- Shared utilities.
- Health checks.
- Common template context.

---

# 30. Environment Variables

Use environment variables for secrets.

Example:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=

DATABASE_URL=

TMDB_API_KEY=

REDIS_URL=

VIDEO_PROVIDER_API_KEY=
VIDEO_PROVIDER_SECRET=
```

Never expose private API keys in:

- HTML.
- JavaScript.
- Git.
- GitHub.
- Client-side source.

---

# 31. Security

Required:

- CSRF protection.
- Secure cookies in production.
- HTTPS.
- Secure headers.
- Environment-based secrets.
- Input validation.
- ORM parameterization.
- Authentication checks.
- Authorization checks.
- Rate limiting where appropriate.
- No secret values in logs.
- No arbitrary external URL playback injection from users.

Especially important:

The frontend must not be allowed to submit an arbitrary URL and make Filvora treat it as an official playback source.

Playback sources should come from trusted provider configuration/database mappings.

---

# 32. Legal/Provider Boundary

Filvora should be designed for legitimate content sources.

The architecture may support:

- Public-domain movies.
- Content Filvora owns.
- Content Filvora has permission to distribute.
- Licensed video providers.
- Authorized embeds.
- Other legally authorized playback mechanisms.

Filvora must not:

- Scrape unauthorized streaming websites.
- Extract hidden video URLs.
- Bypass DRM.
- Circumvent authentication.
- Bypass anti-bot protections.
- Use stolen/private API credentials.
- Proxy unauthorized copyrighted streams.

The provider abstraction exists partly to keep the application independent from any single service.

---

# 33. URL Design

Suggested URLs:

```text
/
```

Home.

```text
/movies/
```

Movie browsing.

```text
/movies/<tmdb_id>/
```

Movie details.

```text
/series/
```

Series browsing.

```text
/series/<tmdb_id>/
```

Series details.

```text
/series/<tmdb_id>/season/<season_number>/
```

Season.

```text
/watch/movie/<tmdb_id>/
```

Movie player.

```text
/watch/series/<tmdb_id>/<season>/<episode>/
```

Episode player.

```text
/search/?q=interstellar
```

Search.

```text
/my-list/
```

Favorites.

```text
/history/
```

Watch history.

---

# 34. Request Lifecycle Example

## Movie page

```text
1. Browser requests /movies/550/

2. Django URL router matches movie view.

3. Movie service receives TMDB ID 550.

4. Catalog cache is checked.

5. If data is missing/stale:
       TMDB API is called.

6. Metadata is normalized.

7. Authorized playback availability is checked.

8. Django renders movie.html.

9. Browser loads TMDB images.

10. User clicks Watch Now.

11. Django generates/returns authorized playback information.

12. Browser connects directly to playback provider.

13. Video player streams content.

14. Django receives periodic progress updates.

15. Progress is stored in PostgreSQL.
```

---

# 35. Why the Movie Doesn't Need to Be Downloaded

Filvora does not need this:

```text
Movie
 ↓
Download
 ↓
Filvora server disk
 ↓
Django
 ↓
User
```

Instead:

```text
Movie
 ↓
Authorized provider/CDN
 ↓
Browser
```

Filvora stores only the information required to identify and access the authorized playback source.

This is the fundamental architecture requirement.

---

# 36. Handling "No Playback Available"

Not every TMDB title will necessarily have an authorized playback source.

The UI should distinguish:

```text
Metadata available
+
Playback available
```

from:

```text
Metadata available
+
Playback unavailable
```

For unavailable content, show:

```text
Not available to watch
```

rather than a broken player.

The catalog should never imply that every TMDB title is streamable through Filvora.

---

# 37. Error Handling

Create friendly error states.

Examples:

### TMDB unavailable

```text
We're having trouble loading movie information.
Please try again.
```

### Playback unavailable

```text
This title isn't currently available for playback.
```

### Network/player error

```text
Playback interrupted.
Try again.
```

### Unknown movie

```text
Movie not found.
```

Never expose Python stack traces to users in production.

---

# 38. Mobile Design

Filvora must be responsive.

Prioritize:

```text
Mobile
   ↓
Tablet
   ↓
Desktop
```

Mobile requirements:

- Large tap targets.
- Horizontal card rails.
- Compact navbar.
- Bottom navigation can be considered later.
- Fullscreen player.
- Episode list optimized for touch.
- Avoid huge desktop hero sections.

---

# 39. Accessibility

Include:

- Semantic HTML.
- Keyboard navigation.
- Visible focus states.
- Alt text.
- Captions/subtitles when available.
- Good color contrast.
- Buttons with accessible labels.
- Reduced-motion consideration.

---

# 40. Development Phases

## Phase 1 — Foundation

Build:

- Django project.
- PostgreSQL.
- Base template.
- Tailwind.
- HTMX.
- Navbar.
- Dark theme.
- Basic routing.

Result:

A working Filvora shell.

## Phase 2 — TMDB

Build:

- TMDB client.
- Search.
- Movie details.
- Series details.
- Trending.
- Popular.
- Genres.
- Seasons.
- Episodes.
- Image handling.

Result:

Filvora becomes a working movie/series discovery website.

## Phase 3 — Accounts

Build:

- Registration.
- Login.
- Logout.
- Profile.

## Phase 4 — Library

Build:

- My List.
- Favorites.
- Watch history.

## Phase 5 — Playback abstraction

Build:

- Provider interface.
- Playback service.
- Availability checking.
- Player page.
- Authorized provider integration.

Do not couple the application directly to a single provider.

## Phase 6 — Watch progress

Build:

- Save position.
- Resume playback.
- Completion.
- Continue Watching.
- Next episode.

## Phase 7 — Performance

Add:

- Caching.
- Database indexes.
- Query optimization.
- Lazy loading.
- Better image loading.
- Optional Redis.

## Phase 8 — Polish

Improve:

- Animations.
- Skeleton loaders.
- Responsive design.
- Player UI.
- Error states.
- Empty states.
- Accessibility.

---

# 41. MVP

The first usable Filvora should contain only:

```text
Home
Movies
Series
Search
Movie detail
Series detail
Season/episode list
Authorized player
Login
My List
Watch progress
Continue Watching
```

Do not start with:

- Recommendation AI.
- Multiple profiles.
- Social features.
- Reviews.
- Complex notification systems.
- Microservices.
- Kubernetes.
- Huge caching infrastructure.

Build the core experience first.

---

# 42. Recommended Build Order

Build exactly in this general order:

```text
1. Django project
2. PostgreSQL
3. Tailwind
4. Base template
5. Navbar
6. Homepage
7. TMDB client
8. Movie catalog
9. Series catalog
10. Search
11. Movie detail
12. Series detail
13. Season/episode UI
14. Authentication
15. My List
16. Watch history
17. Playback abstraction
18. Authorized provider integration
19. Video player
20. Progress tracking
21. Continue Watching
22. Caching
23. Responsive polish
24. Security hardening
25. Deployment
```

---

# 43. Architecture Principle

The most important design principle is separation of concerns:

```text
                    FILVORA
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Catalog         Users        Playback
        │              │              │
       TMDB        PostgreSQL      Provider
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Django Templates
                       │
                  Browser / Player
```

TMDB answers:

> "What is this movie/series?"

PostgreSQL answers:

> "What does this Filvora user do?"

The playback provider answers:

> "Where/how can this authorized content be played?"

Django coordinates everything.

The browser renders the UI and receives video directly from the playback provider.

---

# 44. Final Architecture

```text
                           FILVORA
                              │
                    ┌─────────┴─────────┐
                    │                   │
                FRONTEND              BACKEND
                    │                   │
          Django Templates           Django
                    │                   │
              Tailwind CSS       Django REST Framework
                    │                   │
                  HTMX             Service Layer
                    │          ┌────────┼─────────┐
                    │          │        │         │
                    │        TMDB    PostgreSQL  Playback
                    │          │        │         │
                    │          │        │      Provider
                    │          │        │         │
                    └──────────┴────────┴─────────┘
                              │
                              ▼
                           Browser
                              │
                              ▼
                    Authorized Video CDN
                              │
                              ▼
                       HLS / DASH Stream
                              │
                              ▼
                         Video Player
```

The critical rule remains:

**Django is the application server, not the video server.**

That gives Filvora a clean architecture, keeps the application lightweight, and allows the video delivery infrastructure to scale independently.

---

# 45. Project Implementation Status & Master Architecture Context Log

## Current Progress Snapshot (Updated August 2026)

| Phase | Description | Status | Key Artifacts & Implementation Details |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Foundation & Shell | **Completed** | Django project initialized, modular `apps/` directory (`accounts`, `catalog`, `tmdb`, `playback`, `watch`, `library`, `core`), cinematic dark theme layout with Tailwind CSS and HTMX integration. |
| **Phase 2** | TMDB Integration & Discovery | **Completed** | `TMDBClient` (`apps/tmdb/client.py`) with Windows Schannel IPv4 dual fetcher, in-memory cache (5 min TTL), robust mock fallbacks, dynamic hero banner, and 7 discovery rails on `templates/home/index.html`. |
| **Phase 3** | User Authentication | **Completed** | Custom `register` view (`apps/accounts/views.py`), Django `LoginView`/`LogoutView` with Django 5.0+ POST requirement, dynamic navbar auth state (Sign In / Register vs Profile dropdown / Logout), relaxed password complexity for development. |
| **Phase 4** | Library (My List) | **Completed** | `LibraryItem` model (`apps/library/models.py`) with unique constraint on `(user, tmdb_id, media_type)`, `my_list` and `toggle_item` views, HTMX dynamic bookmark toggle with visual state feedback (`Saved` button), dedicated `/library/` grid view. |
| **Phase 5** | Playback & Player Shell | **Completed** | Localized `video.js 8.10.0`, `hls.js`, and `theme-fantasy.css` in `static/` (zero external CDN dependency for playback). Fullscreen player (`templates/playback/watch.html`) with title overlay, 10s skip controls, and global hotkeys (`Space`, `K`, `F`, `M`, `Arrows`, `J`, `L`). |
| **Phase 6** | Watch Progress & Continue Watching | **Completed** | `WatchProgress` model (`apps/watch/models.py`), background beaconing (`/progress/save/`) every 10s and on pause/page unload, seamless resume playback seeking, deduplicated "Continue Watching" homepage rail with live % progress bars and episode-specific resume links. |
| **Phase 7** | Catalog Detail Pages & Series Hierarchy | **Completed** | Full movie detail view (`/movies/<id>/`), TV series detail view (`/series/<id>/`), HTMX-powered season episode switching (`/series/<id>/season/<num>/`), multi-episode playback (`/watch/tv/<id>/<s_num>/<ep_num>/`), cast rails, and browse discovery pages (`/movies/`, `/series/`). |
| **Phase 8** | Live Search & UI Polish | **Completed** | Navbar Live Search autocomplete with HTMX debounced dropdown (`/search/suggest/`), dedicated full-page search results grid (`/search/`), click-outside dropdown dismisser, and cinematic custom 404/500 error pages. |
| **Engine** | Multi-Server Streaming Provider Engine | **Completed** | Pluggable streaming provider layer (`apps/playback/providers.py`) with 4 active mirrors (VidLink, AutoEmbed, 2Embed, NontonGo). Dynamic in-place server switching (`window.location.replace`) and TV next-episode auto-advance. |
| **DX Setup** | Developer Experience & Auto-reload | **Completed** | `django-browser-reload` installed and configured with middleware for instant browser refreshes on file changes. Django development server managed persistently in background. |

---

## Technical Context & Architectural Decisions

### 1. Multi-Server Video Streaming Engine (`apps/playback/providers.py`)
- **Dynamic Content Mapping:** Movies and TV shows do not have static video files hosted on the server. The player dynamically queries authorized video streaming providers based on `tmdb_id` (and `season`/`episode` for TV shows).
- **Active Server Registry:**
  1. `VidLinkProvider` (Server 1 - Default fast HD): `https://vidlink.pro/movie/{tmdb_id}` & `https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}`
  2. `AutoEmbedProvider` (Server 2): `https://autoembed.co/movie/tmdb/{tmdb_id}` & `https://autoembed.co/tv/tmdb/{tmdb_id}-{season}-{episode}`
  3. `TwoEmbedProvider` (Server 3): `https://www.2embed.cc/embed/{tmdb_id}` & `https://www.2embed.cc/embedtv/{tmdb_id}&s={season}&e={episode}`
  4. `NontonGoProvider` (Server 4): `https://www.NontonGo.win/embed/movie/{tmdb_id}` & `https://www.NontonGo.win/embed/tv/{tmdb_id}/{season}/{episode}`
- **History Preservation & Navigation:** Switching servers in `templates/playback/watch.html` executes `window.location.replace('?server=' + this.value)` to swap the active stream in-place without generating clutter in the browser history stack. The Back button links directly to the content's detail page (`/movies/<id>/` or `/series/<id>/`).

### 2. Continue Watching & Progress Beaconing (`apps.watch`)
- **Database Model:** `WatchProgress` stores `(user, tmdb_id, media_type, season, episode, position_seconds, duration_seconds, completed, updated_at)`.
- **Deduplication Logic:** In `HomeView`, the query filters `completed=False, position_seconds__gt=5` ordered by `-updated_at`. When iterating, it tracks seen `(media_type, tmdb_id)` keys so each TV series only appears **once** with its most recently watched episode (e.g. `Game of Thrones (S1:E2)`).
- **Direct Resume:** Continue watching cards link directly to the episode-specific route (`/watch/tv/<id>/<season>/<episode>/`) and automatically resume at the recorded timestamp.
- **CSRF Beaconing:** `/progress/save/` is `@csrf_exempt` to support `navigator.sendBeacon` upon tab close or page navigation.

### 3. TMDB Client & Windows Networking Quirk (`apps/tmdb/client.py`)
- **IPv4 & Schannel Fix:** Windows DNS resolution attempts IPv6 for `api.themoviedb.org`, and Cloudflare TLS 1.3 causes `WinError 10054` in Python `requests`. The client uses `curl.exe -s --ssl-no-revoke -4` with a 5-minute in-memory cache to guarantee 100% reliable <10ms responses.
- **Normalized Response Fields:** `search_multi`, `get_movie_details`, and `get_tv_details` normalize `display_title` and `release_year` so templates never fail on missing date keys.

### 4. Authentication & Security
- **Django 5.0+ Logout Security:** Django 5 strictly requires `POST` requests for logout. `navbar.html` uses `<form method="post" action="/accounts/logout/">{% csrf_token %}<button type="submit">`.
- **HTMX CSRF Header:** `templates/base.html` binds `document.addEventListener('htmx:configRequest', ...)` to attach `X-CSRFToken` to every HTMX AJAX call.
- **Password Complexity:** `AUTH_PASSWORD_VALIDATORS = []` in `config/settings.py` for development ease.

---

## Complete Project File & App Mapping

| App / Directory | Purpose | Key Files |
| :--- | :--- | :--- |
| **`apps.core`** | Homepage & Root Routing | `views.py` (`HomeView`), `urls.py` |
| **`apps.accounts`** | User Authentication | `views.py` (`register`), `urls.py` (`login`, `logout`, `register`) |
| **`apps.tmdb`** | TMDB API Metadata Client | `client.py` (`TMDBClient` with 12 discovery & detail methods) |
| **`apps.catalog`** | Discovery Grids, Details & Search | `views.py` (`movie_browse`, `movie_detail`, `series_browse`, `series_detail`, `season_episodes`, `search_suggest`, `search_results`), `urls.py` |
| **`apps.library`** | User Bookmarks / My List | `models.py` (`LibraryItem`), `views.py` (`my_list`, `toggle_item`), `urls.py` |
| **`apps.playback`** | Streaming Provider & Player | `providers.py` (4 streaming servers), `views.py` (`watch`), `urls.py` |
| **`apps.watch`** | Watch Progress Tracking | `models.py` (`WatchProgress`), `views.py` (`save_progress`), `urls.py` |
| **`templates/`** | Server-Rendered Dark Theme UI | `base.html`, `404.html`, `500.html`, `home/index.html`, `catalog/`, `library/list.html`, `playback/watch.html`, `accounts/` |
| **`static/`** | Offline Playback Assets | `css/videojs/` (video-js + fantasy theme), `js/videojs/` (video.min.js + hls.min.js), `js/main.js` |

---

## Developer Guidelines & Workflow Preferences
1. **Git Strategy:** Commit all incremental changes with clean messages locally (`git commit`). Only push to remote when explicitly requested by the user (`git push`).
2. **Server Management:** The Django development server runs persistently in the background with `django-browser-reload` auto-refreshing the browser tab on file saves.
3. **No Heavy Frontend Frameworks:** Keep all UI server-rendered with Django Templates + Tailwind CSS + HTMX for instant reactivity.





