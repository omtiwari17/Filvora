from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.library.models import LibraryItem

class LibraryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='libuser', password='password123')

    def test_my_list_requires_login(self):
        response = self.client.get('/library/')
        self.assertEqual(response.status_code, 302)

    def test_my_list_authenticated(self):
        self.client.login(username='libuser', password='password123')
        LibraryItem.objects.create(user=self.user, tmdb_id=157336, media_type='movie')
        response = self.client.get('/library/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('saved_items', response.context)
        self.assertEqual(len(response.context['saved_items']), 1)

    def test_toggle_item_add_and_remove(self):
        self.client.login(username='libuser', password='password123')
        # Add item
        res = self.client.post('/library/toggle/', {'tmdb_id': '157336', 'media_type': 'movie', 'variant': 'card'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(LibraryItem.objects.filter(user=self.user, tmdb_id=157336).exists())
        self.assertIn('In My List', res.content.decode('utf-8'))

        # Toggle item (Remove)
        res_remove = self.client.post('/library/toggle/', {'tmdb_id': '157336', 'media_type': 'movie', 'variant': 'card'})
        self.assertEqual(res_remove.status_code, 200)
        self.assertFalse(LibraryItem.objects.filter(user=self.user, tmdb_id=157336).exists())
        self.assertIn('Add to My List', res_remove.content.decode('utf-8'))

    def test_custom_collection_crud(self):
        self.client.login(username='libuser', password='password123')
        create_res = self.client.post('/library/collection/create/', {
            'name': 'Weekend Marathon',
            'description': 'Sci-Fi binge'
        })
        self.assertEqual(create_res.status_code, 302)
        from apps.library.models import CustomCollection
        col = CustomCollection.objects.filter(user=self.user, name='Weekend Marathon').first()
        self.assertIsNotNone(col)

        delete_res = self.client.post(f'/library/collection/{col.id}/delete/')
        self.assertEqual(delete_res.status_code, 302)
        self.assertFalse(CustomCollection.objects.filter(id=col.id).exists())

    def test_multi_profile_library_isolation(self):
        """Verify that Watchlist and Collections are strictly segregated between profiles."""
        from apps.accounts.models import UserProfile
        p1 = UserProfile.objects.create(user=self.user, name='Parent Profile')
        p2 = UserProfile.objects.create(user=self.user, name='Child Profile', is_kids=True)

        self.client.login(username='libuser', password='password123')

        # Select Profile 1 & save item
        session = self.client.session
        session['active_profile_id'] = p1.id
        session.save()

        self.client.post('/library/toggle/', {'tmdb_id': '157336', 'media_type': 'movie', 'variant': 'card'})
        self.assertTrue(LibraryItem.objects.filter(user=self.user, profile=p1, tmdb_id=157336).exists())

        # Switch to Profile 2 & check My List
        session['active_profile_id'] = p2.id
        session.save()

        res = self.client.get('/library/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['saved_items']), 0)
        self.assertFalse(LibraryItem.objects.filter(user=self.user, profile=p2, tmdb_id=157336).exists())

    def test_add_and_delete_scene_bookmark(self):
        from apps.library.models import SceneBookmark
        self.client.login(username='libuser', password='password123')
        
        # 1. Add Bookmark
        response = self.client.post('/library/bookmark/add/', {
            'tmdb_id': 157336,
            'media_type': 'movie',
            'title': 'Interstellar',
            'position': 5055, # 01:24:15
            'note': 'Docking sequence scene',
            'poster_path': '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['timestamp'], '01:24:15')
        self.assertIn('?t=5055', data['play_url'])

        bm = SceneBookmark.objects.filter(user=self.user, tmdb_id=157336).first()
        self.assertIsNotNone(bm)
        self.assertEqual(bm.formatted_timestamp, '01:24:15')
        self.assertEqual(bm.note, 'Docking sequence scene')

        # 2. Check in Library view
        lib_res = self.client.get('/library/')
        self.assertEqual(lib_res.status_code, 200)
        self.assertIn('bookmarks', lib_res.context)
        self.assertEqual(len(lib_res.context['bookmarks']), 1)

        # 3. Delete Bookmark
        del_res = self.client.post(f'/library/bookmark/{bm.id}/delete/')
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(SceneBookmark.objects.filter(id=bm.id).exists())

    def test_multi_profile_bookmark_isolation(self):
        from apps.accounts.models import UserProfile
        from apps.library.models import SceneBookmark
        p1 = UserProfile.objects.create(user=self.user, name='Viewer 1')
        p2 = UserProfile.objects.create(user=self.user, name='Viewer 2')

        self.client.login(username='libuser', password='password123')
        session = self.client.session
        session['active_profile_id'] = p1.id
        session.save()

        # Add bookmark on Profile 1
        self.client.post('/library/bookmark/add/', {
            'tmdb_id': 245891,
            'media_type': 'movie',
            'title': 'John Wick',
            'position': 1200,
            'note': 'Red Circle scene'
        })
        self.assertTrue(SceneBookmark.objects.filter(user=self.user, profile=p1, tmdb_id=245891).exists())

        # Switch to Profile 2
        session['active_profile_id'] = p2.id
        session.save()

        lib_res = self.client.get('/library/')
        self.assertEqual(lib_res.status_code, 200)
        self.assertEqual(len(lib_res.context['bookmarks']), 0)

