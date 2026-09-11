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
        self.test_records.append({
            'status': 'PASS',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'duration': duration,
            'error': None
        })
        if self.verbose:
            print(f"  {Colors.GREEN}[PASS]{Colors.RESET} {class_name}.{test_name} {Colors.DIM}({duration*1000:.1f}ms){Colors.RESET}")
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
        self.test_records.append({
            'status': 'FAIL',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'duration': duration,
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
        self.test_records.append({
            'status': 'ERROR',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'duration': duration,
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
        self.test_records.append({
            'status': 'SKIP',
            'test': test,
            'name': test_name,
            'class': class_name,
            'category': cat['name'],
            'duration': 0.0,
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
