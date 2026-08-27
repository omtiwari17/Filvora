import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.downloads.models import DownloadJob
from apps.downloads.services.filename import generate_video_filename, sanitize_filename
from apps.downloads.services.manager import DownloadManager

class DownloadsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='downloaduser', password='password123')

    def test_filename_generation_specifications(self):
        # Phase 11 Spec: "Movie Name (Year) [Quality].extension"
        movie_fn = generate_video_filename('movie', 'Interstellar', '2014', quality='1080p', ext='mp4')
        self.assertEqual(movie_fn, 'Interstellar (2014) [1080p].mp4')

        # Phase 11 Spec: "Series Name S01E01 [Quality].extension" (no episode title)
        tv_fn = generate_video_filename('tv', 'Breaking Bad', '2008', season=2, episode=3, quality='720p', ext='mp4')
        self.assertEqual(tv_fn, 'Breaking Bad S02E03 [720p].mp4')

    def test_sanitize_filename(self):
        dirty = 'Star Wars: Episode IV - A New Hope / 1977 * ? < > | "'
        cleaned = sanitize_filename(dirty)
        self.assertNotIn(':', cleaned)
        self.assertNotIn('/', cleaned)
        self.assertNotIn('*', cleaned)

    def test_create_and_dashboard_jobs(self):
        self.client.login(username='downloaduser', password='password123')
        job = DownloadJob.objects.create(
            user=self.user,
            tmdb_id=157336,
            media_type='movie',
            title='Interstellar',
            release_year='2014',
            filename='Interstellar (2014) [1080p].mp4',
            status='READY',
            progress=100.0
        )
        response = self.client.get('/downloads/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('jobs', response.context)
        self.assertEqual(response.context['ready_count'], 1)

    def test_start_download_post(self):
        self.client.login(username='downloaduser', password='password123')
        response = self.client.post('/downloads/start/', {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'quality': '1080p'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DownloadJob.objects.filter(user=self.user, tmdb_id=157336).exists())

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
