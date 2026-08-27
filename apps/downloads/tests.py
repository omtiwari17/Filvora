import os
import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from apps.downloads.models import DownloadJob
from apps.downloads.services.filename import generate_video_filename, sanitize_filename
from apps.downloads.services.storage import (
    get_temp_root, create_job_directory, cleanup_job_directory,
    check_disk_space, format_file_size, get_output_filepath
)
from apps.downloads.services.validator import validate_output
from apps.downloads.services.cleanup import cleanup_job
from apps.downloads.providers.base import DownloadProvider
from apps.downloads.providers.registry import (
    register_provider, find_provider, get_providers,
    get_available_qualities, clear_providers
)


class FilenameTestCase(TestCase):
    """Tests for the deterministic filename service (Phase 11 spec)."""

    def test_movie_filename_spec(self):
        """Spec: 'Movie Name (Year) [Quality].extension'"""
        fn = generate_video_filename('movie', 'Interstellar', '2014', quality='1080p', ext='mp4')
        self.assertEqual(fn, 'Interstellar (2014) [1080p].mp4')

    def test_episode_filename_spec(self):
        """Spec: 'Series Name S01E01 [Quality].extension' — no episode title."""
        fn = generate_video_filename('tv', 'Breaking Bad', '2008', season=2, episode=3, quality='720p', ext='mp4')
        self.assertEqual(fn, 'Breaking Bad S02E03 [720p].mp4')

    def test_movie_without_year(self):
        fn = generate_video_filename('movie', 'Untitled', quality='480p', ext='mp4')
        self.assertEqual(fn, 'Untitled [480p].mp4')

    def test_episode_season_padding(self):
        fn = generate_video_filename('tv', 'Show', season=1, episode=1, quality='1080p', ext='mp4')
        self.assertEqual(fn, 'Show S01E01 [1080p].mp4')

    def test_sanitize_windows_chars(self):
        dirty = 'Star Wars: Episode IV - A New Hope / 1977 * ? < > | "'
        cleaned = sanitize_filename(dirty)
        for char in [':', '/', '*', '?', '<', '>', '|', '"']:
            self.assertNotIn(char, cleaned)

    def test_sanitize_preserves_clean_title(self):
        self.assertEqual(sanitize_filename('Clean Title'), 'Clean Title')


class StorageTestCase(TestCase):
    """Tests for temporary storage management."""

    def test_create_job_directory_structure(self):
        paths = create_job_directory('test-uuid-001')
        self.assertTrue(os.path.isdir(paths['root']))
        self.assertTrue(os.path.isdir(paths['source']))
        self.assertTrue(os.path.isdir(paths['processing']))
        self.assertTrue(os.path.isdir(paths['output']))
        # Cleanup
        shutil.rmtree(paths['root'], ignore_errors=True)

    def test_cleanup_job_directory(self):
        paths = create_job_directory('test-uuid-002')
        self.assertTrue(os.path.isdir(paths['root']))
        cleanup_job_directory('test-uuid-002')
        self.assertFalse(os.path.exists(paths['root']))

    def test_disk_space_check_returns_result(self):
        result = check_disk_space(1024)
        self.assertIn('sufficient', result)
        self.assertIn('available_bytes', result)
        self.assertIn('message', result)

    def test_disk_space_zero_required(self):
        result = check_disk_space(0)
        self.assertTrue(result['sufficient'])

    def test_format_file_size(self):
        self.assertEqual(format_file_size(0), '0 B')
        self.assertEqual(format_file_size(1023), '1023.0 B')
        self.assertIn('KB', format_file_size(1024))
        self.assertIn('MB', format_file_size(1024 * 1024))
        self.assertIn('GB', format_file_size(1024 ** 3))

    def test_output_filepath(self):
        path = get_output_filepath('test-uuid-003', 'movie.mp4')
        self.assertTrue(path.endswith('movie.mp4'))
        self.assertIn('job_test-uuid-003', path)
        # Cleanup
        parent = os.path.dirname(os.path.dirname(path))
        shutil.rmtree(parent, ignore_errors=True)


class ValidatorTestCase(TestCase):
    """Tests for output file validation."""

    def test_nonexistent_file(self):
        result = validate_output('/nonexistent/file.mp4')
        self.assertFalse(result['valid'])
        self.assertIn('does not exist', result['error'])

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            filepath = f.name
        try:
            result = validate_output(filepath)
            self.assertFalse(result['valid'])
            self.assertIn('empty', result['error'])
        finally:
            os.unlink(filepath)

    def test_small_file_rejected(self):
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'x' * 100)
            filepath = f.name
        try:
            result = validate_output(filepath)
            self.assertFalse(result['valid'])
            self.assertIn('small', result['error'])
        finally:
            os.unlink(filepath)

    def test_valid_size_file(self):
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'\x00' * 200000)  # 200KB
            filepath = f.name
        try:
            result = validate_output(filepath)
            # Valid if ffprobe not available (accepts based on size)
            self.assertTrue(result['valid'])
            self.assertEqual(result['file_size'], 200000)
        finally:
            os.unlink(filepath)


class ProviderTestCase(TestCase):
    """Tests for the download provider abstraction."""

    def setUp(self):
        clear_providers()

    def tearDown(self):
        clear_providers()

    def test_register_and_find_provider(self):
        class MockProvider(DownloadProvider):
            @property
            def name(self):
                return 'MockProvider'

            @property
            def priority(self):
                return 10

            def supports_download(self, tmdb_id, media_type, season=None, episode=None):
                return True

            def get_downloadable_source(self, tmdb_id, media_type, season=None, episode=None, quality='1080p'):
                return {'url': 'https://example.com/video.mp4', 'headers': {}, 'quality': quality, 'format': 'mp4', 'estimated_size': 0}

        provider = MockProvider()
        register_provider(provider)
        self.assertEqual(len(get_providers()), 1)
        found = find_provider(123, 'movie')
        self.assertIsNotNone(found)
        self.assertEqual(found.name, 'MockProvider')

    def test_no_provider_returns_none(self):
        found = find_provider(999, 'movie')
        self.assertIsNone(found)

    def test_provider_priority_ordering(self):
        class HighPriority(DownloadProvider):
            @property
            def name(self): return 'High'
            @property
            def priority(self): return 1
            def supports_download(self, *a, **kw): return True
            def get_downloadable_source(self, *a, **kw): return {}

        class LowPriority(DownloadProvider):
            @property
            def name(self): return 'Low'
            @property
            def priority(self): return 100
            def supports_download(self, *a, **kw): return True
            def get_downloadable_source(self, *a, **kw): return {}

        register_provider(LowPriority())
        register_provider(HighPriority())
        found = find_provider(123, 'movie')
        self.assertEqual(found.name, 'High')

    def test_default_qualities(self):
        qualities = get_available_qualities(123, 'movie')
        self.assertEqual(qualities, ['1080p', '720p', '480p'])

    def test_register_invalid_type(self):
        with self.assertRaises(TypeError):
            register_provider("not a provider")


class DownloadJobModelTestCase(TestCase):
    """Tests for the DownloadJob model."""

    def setUp(self):
        self.user = User.objects.create_user(username='dluser', password='pass123')

    def test_create_job(self):
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            release_year='2014',
            filename='Interstellar (2014) [1080p].mp4',
            status='QUEUED',
            progress=0.0
        )
        self.assertEqual(str(job), 'Interstellar (2014) [1080p].mp4 [QUEUED]')
        self.assertEqual(job.media_type, 'movie')

    def test_status_choices(self):
        valid_statuses = ['QUEUED', 'DOWNLOADING', 'PROCESSING', 'READY', 'FAILED', 'CANCELLED']
        for status in valid_statuses:
            job = DownloadJob.objects.create(
                user=self.user,
                tmdb_id=1,
                title='Test',
                status=status
            )
            self.assertEqual(job.status, status)


class DownloadViewsTestCase(TestCase):
    """Tests for download views and URL routing."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='downloaduser', password='password123')

    def test_dashboard_requires_login(self):
        response = self.client.get('/downloads/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.get('/downloads/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('jobs', response.context)
        self.assertIn('active_count', response.context)
        self.assertIn('ready_count', response.context)
        self.assertIn('failed_count', response.context)

    def test_start_download_post(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.post('/downloads/start/', {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'quality': '1080p'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DownloadJob.objects.filter(user=self.user, tmdb_id=157336).exists())

    def test_start_download_get_rejected(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.get('/downloads/start/')
        self.assertEqual(response.status_code, 400)

    def test_cancel_download_job(self):
        self.client.login(username='downloaduser', password='password123')
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            status='DOWNLOADING'
        )
        response = self.client.post(f'/downloads/cancel/{job.id}/')
        self.assertEqual(response.status_code, 302)
        job.refresh_from_db()
        self.assertEqual(job.status, 'CANCELLED')

    def test_retry_download_job(self):
        self.client.login(username='downloaduser', password='password123')
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            status='FAILED',
            error_message='Test error'
        )
        response = self.client.post(f'/downloads/retry/{job.id}/')
        self.assertEqual(response.status_code, 302)
        job.refresh_from_db()
        self.assertEqual(job.status, 'QUEUED')
        self.assertEqual(job.error_message, '')

    def test_delete_completed_job(self):
        self.client.login(username='downloaduser', password='password123')
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            status='READY'
        )
        response = self.client.post(f'/downloads/delete/{job.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(DownloadJob.objects.filter(id=job.id).exists())

    def test_delete_active_job_blocked(self):
        self.client.login(username='downloaduser', password='password123')
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            status='DOWNLOADING'
        )
        response = self.client.post(f'/downloads/delete/{job.id}/')
        self.assertEqual(response.status_code, 302)
        # Should NOT be deleted since it's still active
        self.assertTrue(DownloadJob.objects.filter(id=job.id).exists())

    def test_status_partial(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.get('/downloads/status/')
        self.assertEqual(response.status_code, 200)

    def test_download_dialog(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.get('/downloads/dialog/?tmdb_id=157336&media_type=movie')
        self.assertEqual(response.status_code, 200)

    def test_job_ownership_enforcement(self):
        """Ensure users cannot access other users' jobs."""
        other_user = User.objects.create_user(username='other', password='pass')
        job = DownloadJob.objects.create(
            user=other_user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            status='READY'
        )
        self.client.login(username='downloaduser', password='password123')
        response = self.client.post(f'/downloads/cancel/{job.id}/')
        self.assertEqual(response.status_code, 404)
