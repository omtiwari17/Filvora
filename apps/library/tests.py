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

