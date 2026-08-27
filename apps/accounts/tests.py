from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='accountuser', password='password123')

    def test_profiles_view(self):
        self.client.login(username='accountuser', password='password123')
        response = self.client.get('/accounts/profiles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('profiles', response.context)
        self.assertGreaterEqual(len(response.context['profiles']), 1)

    def test_create_profile(self):
        self.client.login(username='accountuser', password='password123')
        response = self.client.post('/accounts/profiles/create/', {
            'name': 'Kids Profile',
            'is_kids': 'on'
        })
        self.assertEqual(response.status_code, 302)
        kids_profile = UserProfile.objects.filter(user=self.user, name='Kids Profile').first()
        self.assertIsNotNone(kids_profile)
        self.assertTrue(kids_profile.is_kids)

    def test_switch_profile(self):
        self.client.login(username='accountuser', password='password123')
        p = UserProfile.objects.create(user=self.user, name='Guest', is_kids=False)
        response = self.client.get(f'/accounts/profiles/{p.id}/switch/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('active_profile_id'), p.id)

    def test_delete_profile(self):
        self.client.login(username='accountuser', password='password123')
        p1 = UserProfile.objects.create(user=self.user, name='Profile 1')
        p2 = UserProfile.objects.create(user=self.user, name='Profile 2')
        response = self.client.post(f'/accounts/profiles/{p2.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserProfile.objects.filter(id=p2.id).exists())
