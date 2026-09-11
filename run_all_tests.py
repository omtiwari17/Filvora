#!/usr/bin/env python
"""
================================================================================
  FILVORA — MASTER AUTOMATED TEST RUNNER & SYSTEM VERIFICATION ENGINE
================================================================================

  PURPOSE:
  Runs the complete end-to-end test suite for Filvora in a single command,
  testing every active feature, API endpoint, UI button, HTMX interaction,
  security boundary, and background engine across all 7 production applications
  (122 tests; apps.downloads dropped/on hold).

WHICH TESTING METHOD IS BEST FOR FILVORA?
  -----------------------------------------------------------------------------
  Filvora is an event-driven streaming media application combining:
    * Server-rendered templates with HTMX dynamic partial updates.
    * Multi-profile session isolation in SQLite WAL mode.
    * Multi-server iframe video playback (VidLink, VidFast, AutoEmbed, VidSrc, etc.).
    * REST/JSON beacon progress APIs and CSRF auto-healing.
  
  Comparison of Testing Methodologies:
  1. Headless Browser (Selenium / Playwright):
     - PROS: Tests physical browser click events.
     - CONS: Extremely slow (3-5 minutes), high resource consumption, and brittle
       when dealing with external third-party video iframes (cross-origin frame
       security restrictions, ad-blocker interference, network latencies).
  2. Django TestCase + Emulated Client + HTMX Headers:
     - PROS: Lightning fast (<10 seconds for 120+ tests), 100% deterministic,
       tests complete request-response cycle, database transactions, session isolation,
       HTMX fragment swaps, context dictionaries, redirect chains, and security.
     - VERDICT: Django Integration & HTMX Emulation with In-Memory Database
       Isolation is the optimal, most reliable testing methodology for Filvora.
  -----------------------------------------------------------------------------

USAGE:
  python run_all_tests.py                  # Run all tests across active apps (122 tests)
  python run_all_tests.py --verbose        # Show individual test method names & times
  python run_all_tests.py --failfast       # Stop immediately on first failure
  python run_all_tests.py --app accounts   # Run only tests for a specific app
  python run_all_tests.py --category 3     # Run only category 3 (Playback)
  python run_all_tests.py --fast           # Accelerated run with mocked provider checks
================================================================================
"""

import os
import sys
import time
import argparse
import unittest
from unittest.mock import patch

# Enable ANSI escape codes on Windows console
os.system('')

# Configure UTF-8 stdout
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test.runner import DiscoverRunner


# ==============================================================================
# ANSI Color Palette (Strict zero-emoji compliance)
# ==============================================================================
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_CYAN = '\033[46m'


# ==============================================================================
# Functional Test Categories Mapping
# ==============================================================================
CATEGORIES = [
    {
        'id': 1,
        'name': 'Authentication & Multi-Profile System',
        'apps': ['apps.accounts'],
        'description': 'User registration, login/logout, profile CRUD, avatar themes, kids mode profile segregation, switching & cross-user isolation'
    },
    {
        'id': 2,
        'name': 'Catalog, Discovery & Audience Filters',
        'apps': ['apps.catalog'],
        'description': 'Movie/series browsing, audience filters (live action, kids, mature), mega-season chunking, trailers, search & surprise-me'
    },
    {
        'id': 3,
        'name': 'Video Playback, Multi-Server & Failover',
        'apps': ['apps.playback'],
        'description': 'Direct timestamp jumps (?t=), 6-server circular failover sequence, server preferences, resume threshold & TV navigation'
    },
    {
        'id': 4,
        'name': 'Watch History, Ratings & Progress Engine',
        'apps': ['apps.watch'],
        'description': '15s noise filter, completion detection, history timeline rails, 1-5 star user ratings with HTMX swap & analytics breakdowns'
    },
    {
        'id': 5,
        'name': 'Library, Watchlist, Collections & Bookmarks',
        'apps': ['apps.library'],
        'description': 'Watchlist toggles (card/hero), custom collections CRUD, scene timestamp bookmarks with personal notes & HTMX deletes'
    },
    {
        'id': 6,
        'name': 'Core Engine, CSRF Healing & Recommendations',
        'apps': ['apps.core'],
        'description': 'Hero billboard, continue watching rails, affinity recommendations, branded CSRF auto-healing (browser, HTMX, JSON) & PWA'
    },
    {
        'id': 7,
        'name': 'TMDB API Client, Caching & Resilience',
        'apps': ['apps.tmdb'],
        'description': 'TMDB API client requests, in-memory caching, age rating extraction, cross-media genre mapping & zero-emoji compliance'
    },
    # Note: apps.downloads is ON HOLD / DROPPED (Standby offline pipeline deactivated)
]



# ==============================================================================
# Comprehensive Test Descriptions Registry (All 122 Tests across 7 Subsystems)
# ==============================================================================
TEST_DESCRIPTIONS = {
    # --------------------------------------------------------------------------
    # CATEGORY 1: Authentication & Multi-Profile System (apps.accounts)
    # --------------------------------------------------------------------------
    'test_profiles_view': 'Verifies user profiles view renders list of all active user profiles',
    'test_create_profile': 'Verifies profile creation with kids mode flag and avatar generation',
    'test_switch_profile': 'Verifies session active_profile_id updates correctly on profile switch',
    'test_delete_profile': 'Verifies profile deletion and database record cleanup',
    'test_update_profile': 'Verifies updating profile name, avatar theme color and kids mode setting',
    'test_register_view_get': 'Verifies registration GET view renders form and fields correctly',
    'test_register_valid_submission': 'Verifies user registration, password hashing and default profile auto-creation',
    'test_register_invalid_submission': 'Verifies validation failure and error handling on mismatched passwords',
    'test_delete_last_remaining_profile_prevented': 'Ensures user is safely prevented from deleting their sole remaining profile',
    'test_cross_user_profile_access_forbidden': 'Enforces security boundary preventing users from switching or deleting others profiles (404)',
    'test_unauthenticated_profiles_redirect': 'Enforces login redirect when unauthenticated user accesses /accounts/profiles/',

    # --------------------------------------------------------------------------
    # CATEGORY 2: Catalog, Discovery & Audience Filters (apps.catalog)
    # --------------------------------------------------------------------------
    'test_movie_browse': 'Verifies /movies/ catalog browsing, pagination and context payload',
    'test_movie_detail': 'Verifies /movies/<id>/ detail view context and age rating metadata',
    'test_series_browse': 'Verifies /series/ TV catalog browsing, pagination and context payload',
    'test_series_detail': 'Verifies /series/<id>/ TV detail view with seasons and creators context',
    'test_season_episodes': 'Verifies /series/<id>/season/<num>/ HTMX episode list rendering',
    'test_search_results': 'Verifies /search/ multi-entity search query parsing and results',
    'test_search_with_age_rating': 'Verifies search query age rating badges (PG, PG-13, R, TV-MA)',
    'test_search_standalone_rating_query': 'Verifies searching directly for age certification strings',
    'test_search_suggest': 'Verifies /search/suggest/ live HTMX autocomplete dropdown suggestions',
    'test_gta_vi_search_and_detail': 'Verifies special-case catalog search and detail handling',
    'test_discover_view': 'Verifies multi-faceted /discover/ filter engine and media parameters',
    'test_surprise_me_redirect': 'Verifies /surprise-me/ randomizer redirect to movie playback',
    'test_genres_view': 'Verifies /genres/ hub genre grid and category grouping',
    'test_discover_with_language_and_certification': 'Verifies /discover/ filtering by ISO language and certification',
    'test_kids_profile_discover_enforcement': 'Enforces strict certification.lte=PG content filtering for Kids profiles',
    'test_person_detail_view': 'Verifies /person/<id>/ cast/crew filmography showcase',
    'test_trailer_api': 'Verifies /trailer/movie/<id>/ JSON trailer key extraction',
    'test_movie_detail_trailer_context': 'Verifies trailer preview payload is attached to movie detail context',
    'test_franchise_collection_context': 'Verifies official TMDB franchise/saga collection detection and timeline rail',
    'test_movie_browse_with_audience_filter': 'Verifies audience filter segmentation (live action, kids, mature) on movies',
    'test_series_browse_with_tv_genre_and_audience': 'Verifies cross-universe TV genre resolution and audience filtering',
    'test_genres_view_with_tv_type': 'Verifies /genres/?type=tv dual-universe TV genre grid',
    'test_mega_season_partitioning': 'Partitions mega-seasons (>100 eps) into 100-episode virtual volumes with recalculated runtimes',
    'test_standard_season_partitioning': 'Preserves standard 1:1 season numbering for normal TV shows (<100 eps)',
    'test_tmkoc_series_detail_and_season_episodes': 'Verifies 4,800+ episode mega-season partitioning on Taarak Mehta Ka Ooltah Chashmah',
    'test_search_empty_query': 'Verifies safe handling of empty search queries without exceptions',
    'test_trailer_api_tv_series': 'Verifies /trailer/tv/<id>/ JSON trailer key extraction for TV series',
    'test_surprise_me_tv_type': 'Verifies /surprise-me/?type=tv randomizer redirects to TV series page',
    'test_movie_browse_sort_ratings': 'Verifies /movies/ sorting by vote_average.desc',

    # --------------------------------------------------------------------------
    # CATEGORY 3: Video Playback, Multi-Server & Failover (apps.playback)
    # --------------------------------------------------------------------------
    'test_watch_requires_login': 'Enforces authentication redirect on /watch/ streaming endpoints',
    'test_watch_movie_authenticated': 'Verifies movie streaming player initialization and server context',
    'test_watch_direct_jump_timestamp': 'Verifies ?t=<sec> direct timestamp jump injecting multi-protocol embed params',
    'test_watch_series_episode': 'Verifies TV episodic player context, season/episode navigation and next episode',
    'test_provider_registry_priority_and_fallback': 'Verifies 6-server provider priority ordering and fallback chain resolution',
    'test_sticky_server_preference': 'Verifies user-preferred playback server memory and auto-selection',
    'test_report_server_success_endpoint': 'Verifies POST /watch/server-success/ sticky provider preference persistence',
    'test_diagnostics_endpoint': 'Verifies /watch/diagnostics/ streaming server health check (HTML & JSON)',
    'test_player_resume_formatting_and_episode_navigation': 'Verifies resume timestamp badge formatting and previous/next episode links',
    'test_auto_failover_circular_sequence': 'Verifies seamless 6-node failover cycle (VidLink -> VidFast -> AutoEmbed -> VidSrc -> 2Embed -> NontonGo)',
    'test_watch_view_with_auto_failover_parameter': 'Verifies incoming auto-switched requests render HUD banner with countdown',
    'test_watch_view_preserves_timestamp_on_auto_failover': 'Verifies auto-failover carries active playback timestamp into replacement server embed URL',
    'test_report_server_success_missing_payload': 'Verifies 400 rejection on malformed server-success payload',
    'test_report_server_success_get_rejected': 'Verifies GET method rejection on server-success endpoint',
    'test_multi_profile_server_preference_isolation': 'Enforces profile-isolated streaming server preferences between profiles',
    'test_all_providers_movie_and_tv_urls': 'Verifies valid movie and TV embed URL generation across all 6 streaming providers',

    # --------------------------------------------------------------------------
    # CATEGORY 4: Watch History, Ratings & Progress Engine (apps.watch)
    # --------------------------------------------------------------------------
    'test_save_progress_json': 'Verifies POST /watch/progress/ saves playback position and duration',
    'test_save_progress_completed_threshold': 'Verifies watch completion flag trigger at >=90% progress',
    'test_remove_progress_htmx': 'Verifies HTMX single-item watch progress removal from history timeline',
    'test_history_view': 'Verifies /history/ dual-tab timeline rails (Today, Yesterday, Earlier) and rated titles',
    'test_clear_history': 'Verifies POST /history/clear/ purges watch progress for active profile',
    'test_analytics_view': 'Verifies /analytics/ Wrapped dashboard metrics and genre stats',
    'test_analytics_view_season_breakdown': 'Verifies TV season runtime aggregation and season breakdown badges in analytics',
    'test_rate_content_json': 'Verifies POST /watch/rate/ stores 1-5 star user rating',
    'test_rate_content_update': 'Verifies in-place star rating score updates for rated content',
    'test_rate_content_invalid_score': 'Verifies rejection of invalid star rating score (>5)',
    'test_rate_content_zero_score': 'Verifies rejection of 0 star rating score',
    'test_remove_rating': 'Verifies POST /watch/rate/remove/ deletes user rating',
    'test_rate_requires_login': 'Enforces authentication redirect on rating endpoints',
    'test_rate_tv_series': 'Verifies star rating support for TV series media',
    'test_unique_constraint': 'Enforces unique rating per user profile and media item',
    'test_multi_profile_history_and_ratings_isolation': 'Enforces strict isolation of watch history, progress and ratings between user profiles',
    'test_save_progress_below_threshold_ignored': 'Enforces 15s noise filter: progress under 15 seconds is ignored',
    'test_save_progress_tv_series': 'Verifies TV episodic progress tracking with season and episode numbers',
    'test_save_progress_get_rejected': 'Verifies GET method rejection on /watch/progress/',
    'test_clear_history_get_safely_redirects': 'Verifies GET request to /history/clear/ safely redirects to history without clearing',
    'test_rate_content_missing_fields': 'Verifies 400 rejection on rating submission with missing fields',
    'test_rate_content_htmx_partial': 'Verifies HTMX star rating widget partial swap with updated score',

    # --------------------------------------------------------------------------
    # CATEGORY 5: Library, Watchlist, Collections & Bookmarks (apps.library)
    # --------------------------------------------------------------------------
    'test_my_list_requires_login': 'Enforces authentication redirect on /library/ endpoint',
    'test_my_list_authenticated': 'Verifies /library/ displays saved Watchlist items for active profile',
    'test_toggle_item_add_and_remove': 'Verifies HTMX Watchlist toggle button adds and removes items dynamically',
    'test_custom_collection_crud': 'Verifies custom collection playlist creation, listing and deletion',
    'test_multi_profile_library_isolation': 'Enforces strict segregation of Watchlists and Collections between user profiles',
    'test_add_and_delete_scene_bookmark': 'Verifies adding and deleting scene bookmarks with exact seconds and notes',
    'test_unauthenticated_scene_bookmark_returns_401': 'Enforces 401 Unauthorized for unauthenticated bookmark requests',
    'test_multi_profile_bookmark_isolation': 'Enforces profile-isolated scene bookmarks between user profiles',
    'test_toggle_item_hero_variant': 'Verifies hero billboard Watchlist button variant toggle',
    'test_toggle_item_missing_params': 'Verifies 400 rejection when tmdb_id or media_type is missing',
    'test_toggle_item_unauthenticated': 'Enforces login redirect on unauthenticated watchlist toggle',
    'test_add_bookmark_tv_episode': 'Verifies scene bookmark creation for specific TV season and episode',
    'test_delete_bookmark_htmx': 'Verifies HTMX inline deletion of scene bookmark',
    'test_delete_collection_cross_user_forbidden': 'Enforces security boundary preventing users from deleting others collections (404)',

    # --------------------------------------------------------------------------
    # CATEGORY 6: Core Engine, CSRF Healing & Recommendations (apps.core)
    # --------------------------------------------------------------------------
    'test_home_view_anonymous': 'Verifies homepage billboard, trending, popular and upcoming rails for guests',
    'test_home_view_authenticated_with_continue_watching': 'Verifies Continue Watching rail and affinity recommendations on home',
    'test_home_view_with_my_list_preview': 'Verifies Watchlist quick preview rail on homepage',
    'test_recommendation_engine_affinity': 'Verifies affinity scoring engine (+5 for 4-5 stars, +2 for 3 stars, -2 penalty)',
    'test_pwa_assets_and_manifest': 'Verifies PWA manifest.json standalone config, sw.js service worker and link tags',
    'test_csrf_failure_view_browser': 'Verifies branded 403 CSRF recovery view, auto-cookie renewal and 3s countdown',
    'test_csrf_failure_view_htmx': 'Verifies HTMX CSRF recovery response issuing HX-Refresh header and fresh cookie',
    'test_csrf_failure_view_json': 'Verifies JSON CSRF recovery response with error status and renewed cookie',
    'test_csrf_settings_configuration': 'Verifies CSRF failure handler, SameSite=Lax, and CSRF_TRUSTED_ORIGINS settings',
    'test_404_handler': 'Verifies custom 404 handler for non-existent routes',
    'test_kids_mode_homepage_content_filtering': 'Verifies homepage content curation for active Kids profile',
    'test_recommendations_with_empty_history': 'Verifies fallback recommendation behavior for users with zero watch history',

    # --------------------------------------------------------------------------
    # CATEGORY 7: TMDB API Client, Caching & Resilience (apps.tmdb)
    # --------------------------------------------------------------------------
    'test_mock_movies_fallback': 'Verifies offline mock movies fallback dataset contains valid catalog entries',
    'test_mock_series_fallback': 'Verifies offline mock TV series fallback dataset contains valid series entries',
    'test_attach_age_rating_movie': 'Verifies movie age certification heuristic mapping (animation->PG, horror->R)',
    'test_attach_age_rating_tv': 'Verifies TV age certification heuristic mapping (drama/crime->TV-MA)',
    'test_get_movie_details': 'Verifies TMDB movie details retrieval with age rating metadata attached',
    'test_search_categorized': 'Verifies categorized multi-search partitioning into movies, series and people',
    'test_get_genres_list': 'Verifies official TMDB genre list retrieval',
    'test_discover_content': 'Verifies content discovery filtering by mood and media type',
    'test_get_surprise_title': 'Verifies random surprise title selection algorithm',
    'test_discover_content_with_filters': 'Verifies faceted discovery with language, certification and kids-only filters',
    'test_get_content_rating_and_cache': 'Verifies age rating caching in TMDBClient._RATING_CACHE',
    'test_get_genres_list_tv_and_zero_emojis': 'Verifies TV genre list retrieval and enforces strict zero-emoji compliance',
    'test_genre_resolution_cross_media': 'Verifies multi-directional cross-media genre mapping between Movies and TV',
    'test_discover_content_audience_filters': 'Verifies TMDB query audience segment filtering (live action vs kids family)',
    'test_tv_certification_conversion': 'Verifies safe translation of MPAA ratings to TV certifications (R -> TV-MA)',
    'test_get_tv_details': 'Verifies TMDB TV series details retrieval with metadata attached',
    'test_get_series_season': 'Verifies TMDB season episode list retrieval and structure',
    'test_search_multi_empty': 'Verifies empty string search returns empty list safely without API calls',
}


def get_test_description(test, test_name, class_name):
    """Retrieve human-readable description for a test case."""
    # 1. Check custom explicit docstring if available
    doc = getattr(getattr(test, test_name, None), '__doc__', None)
    if doc:
        clean_doc = doc.strip().splitlines()[0].strip()
        if clean_doc:
            return clean_doc

    # 2. Check curated dictionary
    if test_name in TEST_DESCRIPTIONS:
        return TEST_DESCRIPTIONS[test_name]

    # 3. Dynamic formatting fallback
    name_clean = test_name
    if name_clean.startswith('test_'):
        name_clean = name_clean[5:]
    readable = name_clean.replace('_', ' ').strip().capitalize()
    return f"Verifies {readable.lower()}"


def get_category_for_test(test):
    """Determine category dictionary for a given test case."""
    module = getattr(test, '__module__', '')
    for cat in CATEGORIES:
        for app in cat['apps']:
            if app in module or module.startswith(app):
                return cat
    return {
        'id': 99,
        'name': 'General Integration Tests',
        'apps': [module],
        'description': 'Miscellaneous project integration tests'
    }


# ==============================================================================
# Custom Test Result Collector & Formatter
# ==============================================================================
class CategorizedTestResult(unittest.TestResult):
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose
        self.test_records = []
        self.category_stats = {cat['id']: {
            'name': cat['name'],
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errored': 0,
            'skipped': 0,
            'duration': 0.0
        } for cat in CATEGORIES}
        self.category_stats[99] = {
            'name': 'General Integration Tests',
            'total': 0, 'passed': 0, 'failed': 0, 'errored': 0, 'skipped': 0, 'duration': 0.0
        }
        self._test_start_time = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._test_start_time = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        duration = time.time() - self._test_start_time
        cat = get_category_for_test(test)
        cat_id = cat['id']
        self.category_stats[cat_id]['total'] += 1
        self.category_stats[cat_id]['passed'] += 1
        self.category_stats[cat_id]['duration'] += duration

        test_name = test._testMethodName
        class_name = test.__class__.__name__
        desc = get_test_description(test, test_name, class_name)
        self.test_records.append({
            'status': 'PASS',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'category_id': cat_id,
            'duration': duration,
            'description': desc,
            'error': None
        })
        if self.verbose:
            dur_str = f"{duration*1000:.1f}ms" if duration < 1.0 else f"{duration:.2f}s"
            print(f"  {Colors.GREEN}[PASS]{Colors.RESET} {class_name}.{test_name} {Colors.DIM}({dur_str}){Colors.RESET}")
        else:
            sys.stdout.write(f"{Colors.GREEN}.{Colors.RESET}")
            sys.stdout.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        duration = time.time() - self._test_start_time
        cat = get_category_for_test(test)
        cat_id = cat['id']
        self.category_stats[cat_id]['total'] += 1
        self.category_stats[cat_id]['failed'] += 1
        self.category_stats[cat_id]['duration'] += duration

        test_name = test._testMethodName
        class_name = test.__class__.__name__
        desc = get_test_description(test, test_name, class_name)
        self.test_records.append({
            'status': 'FAIL',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'category_id': cat_id,
            'duration': duration,
            'description': desc,
            'error': self._exc_info_to_string(err, test)
        })
        if self.verbose:
            print(f"\n  {Colors.RED}[FAIL]{Colors.RESET} {class_name}.{test_name}")
        else:
            sys.stdout.write(f"{Colors.RED}F{Colors.RESET}")
            sys.stdout.flush()

    def addError(self, test, err):
        super().addError(test, err)
        duration = time.time() - self._test_start_time
        cat = get_category_for_test(test)
        cat_id = cat['id']
        self.category_stats[cat_id]['total'] += 1
        self.category_stats[cat_id]['errored'] += 1
        self.category_stats[cat_id]['duration'] += duration

        test_name = test._testMethodName
        class_name = test.__class__.__name__
        desc = get_test_description(test, test_name, class_name)
        self.test_records.append({
            'status': 'ERROR',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'category_id': cat_id,
            'duration': duration,
            'description': desc,
            'error': self._exc_info_to_string(err, test)
        })
        if self.verbose:
            print(f"\n  {Colors.RED}[ERROR]{Colors.RESET} {class_name}.{test_name}")
        else:
            sys.stdout.write(f"{Colors.RED}E{Colors.RESET}")
            sys.stdout.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        cat = get_category_for_test(test)
        cat_id = cat['id']
        self.category_stats[cat_id]['total'] += 1
        self.category_stats[cat_id]['skipped'] += 1

        test_name = test._testMethodName
        class_name = test.__class__.__name__
        desc = get_test_description(test, test_name, class_name)
        self.test_records.append({
            'status': 'SKIP',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'category_id': cat_id,
            'duration': 0.0,
            'description': desc,
            'error': reason
        })
        if self.verbose:
            print(f"  {Colors.YELLOW}[SKIP]{Colors.RESET} {class_name}.{test_name} ({reason})")
        else:
            sys.stdout.write(f"{Colors.YELLOW}S{Colors.RESET}")
            sys.stdout.flush()



# ==============================================================================
# Custom Test Runner Harness
# ==============================================================================
class FilvoraTestRunner(DiscoverRunner):
    def __init__(self, custom_result=None, **kwargs):
        super().__init__(**kwargs)
        self.custom_result = custom_result

    def run_suite(self, suite, **kwargs):
        return suite.run(self.custom_result)


# ==============================================================================
# Terminal Presentation Functions
# ==============================================================================
def print_banner():
    width = 86
    print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}   FILVORA AUTOMATED MASTER TEST SUITE & ARCHITECTURE VERIFIER{Colors.RESET}")
    print(f"{Colors.DIM}   Django 5.2+ | SQLite WAL | Multi-Profile | 6-Server Failover | Strict SVG{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}\n")


def print_categories_overview(selected_cat_id=None, selected_app=None):
    print(f"{Colors.BOLD}Architectural Test Categories Loaded:{Colors.RESET}")
    for cat in CATEGORIES:
        marker = " "
        if selected_cat_id and cat['id'] == selected_cat_id:
            marker = f"{Colors.GREEN}>{Colors.RESET}"
        elif selected_app and any(selected_app in a for a in cat['apps']):
            marker = f"{Colors.GREEN}>{Colors.RESET}"
        print(f"  {marker} [{cat['id']}] {Colors.BOLD}{cat['name']:<46}{Colors.RESET} {Colors.DIM}({', '.join(cat['apps'])}){Colors.RESET}")
    print()


def print_scorecard_table(category_stats, total_duration):
    width = 86
    print(f"\n\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}   TEST EXECUTION SCORECARD BY SUBSYSTEM{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}")

    header = f"| {'#':<2} | {'Category / Functional Subsystem':<42} | {'Tests':<5} | {'Pass':<4} | {'Fail':<4} | {'Err':<3} | {'Time':<7} | {'Health':<6} |"
    divider = f"+----+{'-' * 44}+{'-' * 7}+{'-' * 6}+{'-' * 6}+{'-' * 5}+{'-' * 9}+{'-' * 8}+"

    print(divider)
    print(header)
    print(divider)

    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errored = 0

    for cat in CATEGORIES:
        cid = cat['id']
        stats = category_stats.get(cid, {})
        c_tot = stats.get('total', 0)
        c_pass = stats.get('passed', 0)
        c_fail = stats.get('failed', 0)
        c_err = stats.get('errored', 0)
        c_time = stats.get('duration', 0.0)

        total_tests += c_tot
        total_passed += c_pass
        total_failed += c_fail
        total_errored += c_err

        if c_tot == 0:
            status_str = f"{Colors.DIM}N/A{Colors.RESET}"
        elif c_fail == 0 and c_err == 0:
            status_str = f"{Colors.GREEN}OK{Colors.RESET}"
        else:
            status_str = f"{Colors.RED}FAIL{Colors.RESET}"

        name_display = cat['name']
        if len(name_display) > 42:
            name_display = name_display[:39] + '...'

        print(f"| {cid:<2} | {name_display:<42} | {c_tot:<5} | {c_pass:<4} | {c_fail:<4} | {c_err:<3} | {c_time:<6.2f}s | {status_str:<15} |")

    print(divider)

    overall_status = f"{Colors.GREEN}100% PASS{Colors.RESET}" if (total_failed == 0 and total_errored == 0) else f"{Colors.RED}ISSUES DETECTED{Colors.RESET}"
    total_row = f"|    | {Colors.BOLD}{'TOTAL / SYSTEM-WIDE VERIFICATION':<42}{Colors.RESET} | {total_tests:<5} | {total_passed:<4} | {total_failed:<4} | {total_errored:<3} | {total_duration:<6.2f}s | {overall_status:<24} |"
    print(total_row)
    print(divider)


def print_detailed_category_breakdown(test_records, category_stats):
    """Print detailed list of tests for each category with human-readable descriptions and timings."""
    width = 86
    print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}   DETAILED ARCHITECTURAL TEST BREAKDOWN BY SUBSYSTEM{Colors.RESET}")
    print(f"{Colors.DIM}   Every test case verified, its functional purpose and execution time{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}")

    # Group test records by category_id
    records_by_cat = {}
    for r in test_records:
        cid = r.get('category_id', 99)
        records_by_cat.setdefault(cid, []).append(r)

    for cat in CATEGORIES:
        cid = cat['id']
        tests = records_by_cat.get(cid, [])
        if not tests:
            continue

        c_pass = sum(1 for t in tests if t['status'] == 'PASS')
        c_fail = sum(1 for t in tests if t['status'] == 'FAIL')
        c_err = sum(1 for t in tests if t['status'] == 'ERROR')
        c_tot = len(tests)
        c_time = sum(t['duration'] for t in tests)

        if c_fail == 0 and c_err == 0:
            health_badge = f"{Colors.GREEN}[{c_pass}/{c_tot} PASSED]{Colors.RESET}"
        else:
            health_badge = f"{Colors.RED}[{c_fail + c_err} FAILED / {c_tot} TOTAL]{Colors.RESET}"

        print(f"\n{Colors.BOLD}{Colors.CYAN}--- CATEGORY [{cid}] {cat['name'].upper()} {health_badge} ({c_time:.2f}s) ---{Colors.RESET}")
        print(f"{Colors.DIM}    Subsystem: {cat['description']}{Colors.RESET}")
        print(f"{Colors.DIM}    {'-' * 80}{Colors.RESET}")

        for t in tests:
            status = t['status']
            if status == 'PASS':
                status_badge = f"{Colors.GREEN}[PASS]{Colors.RESET}"
            elif status == 'FAIL':
                status_badge = f"{Colors.RED}[FAIL]{Colors.RESET}"
            elif status == 'ERROR':
                status_badge = f"{Colors.MAGENTA}[ERR]{Colors.RESET}"
            else:
                status_badge = f"{Colors.YELLOW}[SKIP]{Colors.RESET}"

            dur_str = f"{t['duration']*1000:.1f}ms" if t['duration'] < 1.0 else f"{t['duration']:.2f}s"
            print(f"  {status_badge}  {Colors.BOLD}{t['name']}{Colors.RESET} {Colors.DIM}({dur_str}){Colors.RESET}")
            print(f"          {Colors.WHITE}{t['description']}{Colors.RESET}")

    # General Integration Tests (if any)
    gen_tests = records_by_cat.get(99, [])
    if gen_tests:
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- GENERAL INTEGRATION TESTS [{len(gen_tests)} Tests] ---{Colors.RESET}")
        for t in gen_tests:
            status = t['status']
            if status == 'PASS':
                status_badge = f"{Colors.GREEN}[PASS]{Colors.RESET}"
            elif status == 'FAIL':
                status_badge = f"{Colors.RED}[FAIL]{Colors.RESET}"
            elif status == 'ERROR':
                status_badge = f"{Colors.MAGENTA}[ERR]{Colors.RESET}"
            else:
                status_badge = f"{Colors.YELLOW}[SKIP]{Colors.RESET}"
            dur_str = f"{t['duration']*1000:.1f}ms" if t['duration'] < 1.0 else f"{t['duration']:.2f}s"
            print(f"  {status_badge}  {Colors.BOLD}{t['name']}{Colors.RESET} {Colors.DIM}({dur_str}){Colors.RESET}")
            print(f"          {Colors.WHITE}{t['description']}{Colors.RESET}")

    print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")


def print_failures_and_errors(test_records):
    failures = [r for r in test_records if r['status'] in ('FAIL', 'ERROR')]
    if not failures:
        return

    width = 86
    print(f"\n{Colors.RED}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.RED}   DETAILED FAILURE & ERROR DIAGNOSTICS ({len(failures)} item(s)){Colors.RESET}")
    print(f"{Colors.RED}{'=' * width}{Colors.RESET}\n")

    for idx, f in enumerate(failures, 1):
        status_color = Colors.RED if f['status'] == 'FAIL' else Colors.MAGENTA
        print(f"[{idx}] {status_color}[{f['status']}]{Colors.RESET} {Colors.BOLD}{f['class']}.{f['name']}{Colors.RESET}")
        print(f"    Category: {f['category']}")
        print(f"    Duration: {f['duration']:.3f}s")
        print(f"{Colors.DIM}{'-' * 70}{Colors.RESET}")
        if f['error']:
            for line in f['error'].strip().splitlines():
                print(f"    {line}")
        print(f"{Colors.DIM}{'-' * 70}{Colors.RESET}\n")


def print_final_status(total_tests, total_passed, total_failed, total_errored, total_duration):
    width = 86
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0

    print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
    if total_failed == 0 and total_errored == 0 and total_tests > 0:
        print(f"{Colors.BOLD}{Colors.GREEN}   [PASS] 100% OF TESTS PASSED ({total_passed}/{total_tests}) IN {total_duration:.2f}s{Colors.RESET}")
        print(f"{Colors.GREEN}   STATUS: ALL APPS, APIS, BUTTONS & FAILOVER ENGINES HEALTHY{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.RED}   [FAIL] {total_failed + total_errored} TESTS FAILED OUT OF {total_tests} ({pass_rate:.1f}% PASS RATE){Colors.RESET}")
        print(f"{Colors.RED}   STATUS: ATTENTION REQUIRED - SEE DIAGNOSTICS ABOVE{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}\n")


# ==============================================================================
# Main Execution Entrypoint
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Filvora Master Test Suite & Feature Verification Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output showing every test method and execution duration")
    parser.add_argument('--failfast', '-x', action='store_true', help="Stop testing immediately on first failure or error")
    parser.add_argument('--app', type=str, default=None, help="Run tests for a specific app (e.g. accounts, catalog, playback, watch, library, downloads, core, tmdb)")
    parser.add_argument('--category', type=int, default=None, help="Run tests for a specific numerical category (1 to 8)")
    parser.add_argument('--fast', action='store_true', help="Fast mode: mocks external network probes for sub-second test execution")

    args = parser.parse_args()

    print_banner()
    if args.fast:
        print(f"  {Colors.YELLOW}[+] Fast Mode Enabled: Mocking external provider network probes for accelerated execution.{Colors.RESET}\n")

    # Determine test labels
    test_labels = []
    if args.category:
        cat_match = next((c for c in CATEGORIES if c['id'] == args.category), None)
        if not cat_match:
            print(f"{Colors.RED}Error: Category {args.category} not found. Available categories: 1 to 7.{Colors.RESET}")
            sys.exit(1)
        test_labels = [f"{app}.tests" for app in cat_match['apps']]
        print_categories_overview(selected_cat_id=args.category)
    elif args.app:
        target_app = args.app.strip().lower()
        if not target_app.startswith('apps.'):
            target_app = f"apps.{target_app}"
        test_labels = [f"{target_app}.tests"]
        print_categories_overview(selected_app=target_app)
    else:
        test_labels = [
            'apps.accounts.tests',
            'apps.catalog.tests',
            'apps.playback.tests',
            'apps.watch.tests',
            'apps.library.tests',
            # 'apps.downloads.tests',  # [ON HOLD / DROPPED]
            'apps.core.tests',
            'apps.tmdb.tests',
        ]
        print_categories_overview()

    print(f"{Colors.BOLD}Target Suites: {Colors.CYAN}{', '.join(test_labels)}{Colors.RESET}")
    print(f"{Colors.DIM}Executing tests in transaction-isolated SQLite test database...{Colors.RESET}\n")

    # Instantiate custom result and runner
    custom_result = CategorizedTestResult(verbose=args.verbose)
    runner = FilvoraTestRunner(
        custom_result=custom_result,
        verbosity=0,
        failfast=args.failfast,
        interactive=False
    )

    runner.setup_test_environment()
    old_db_config = runner.setup_databases()

    start_wall_time = time.time()

    # Patches to protect database and accelerate runs
    patches = []
    if args.fast:
        from apps.playback.providers import PlaybackProvider
        patches.append(
            patch.object(PlaybackProvider, 'check_health', return_value={'status': 'healthy', 'latency_ms': 8.5, 'error': None})
        )

    for p in patches:
        p.start()

    try:
        suite = runner.build_suite(test_labels)
        runner.run_suite(suite)
    finally:
        for p in patches:
            p.stop()

    total_duration = time.time() - start_wall_time


    # Tear down test database
    runner.teardown_databases(old_db_config)
    runner.teardown_test_environment()

    # Print results
    print_scorecard_table(custom_result.category_stats, total_duration)
    print_detailed_category_breakdown(custom_result.test_records, custom_result.category_stats)
    print_failures_and_errors(custom_result.test_records)

    total_tests = len(custom_result.test_records)
    total_passed = sum(1 for r in custom_result.test_records if r['status'] == 'PASS')
    total_failed = sum(1 for r in custom_result.test_records if r['status'] == 'FAIL')
    total_errored = sum(1 for r in custom_result.test_records if r['status'] == 'ERROR')

    print_final_status(total_tests, total_passed, total_failed, total_errored, total_duration)

    # Standard exit code for CI/automation
    if total_failed > 0 or total_errored > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
