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

    def test_update_profile(self):
        self.client.login(username='accountuser', password='password123')
        p = UserProfile.objects.create(user=self.user, name='Original Name', is_kids=False)
        response = self.client.post(f'/accounts/profiles/{p.id}/update/', {
            'name': 'Updated Name',
            'is_kids': 'on',
            'avatar_color': '3b82f6'
        })
        self.assertEqual(response.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.name, 'Updated Name')
        self.assertTrue(p.is_kids)
        self.assertIn('3b82f6', p.avatar)

    def test_register_view_get(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_register_valid_submission(self):
        response = self.client.post('/accounts/register/', {
            'username': 'newuser123',
            'password1': 'SecretP@ssword123!',
            'password2': 'SecretP@ssword123!'
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.filter(username='newuser123').first()
        self.assertIsNotNone(new_user)
        # Default profile auto-created
        profile = UserProfile.objects.filter(user=new_user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, 'Newuser123')
        self.assertEqual(self.client.session.get('active_profile_id'), profile.id)

    def test_register_invalid_submission(self):
        response = self.client.post('/accounts/register/', {
            'username': 'baduser',
            'password1': 'passwordOne',
            'password2': 'passwordMismatch'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_delete_last_remaining_profile_prevented(self):
        self.client.login(username='accountuser', password='password123')
        # Ensure only 1 profile exists
        UserProfile.objects.filter(user=self.user).delete()
        sole_profile = UserProfile.objects.create(user=self.user, name='Sole Profile')
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)
        # Attempt delete
        response = self.client.post(f'/accounts/profiles/{sole_profile.id}/delete/')
        self.assertEqual(response.status_code, 302)
        # Profile still exists because count was 1
        self.assertTrue(UserProfile.objects.filter(id=sole_profile.id).exists())

    def test_cross_user_profile_access_forbidden(self):
        other_user = User.objects.create_user(username='otheruser', password='password123')
        other_profile = UserProfile.objects.create(user=other_user, name='Other Profile')
        self.client.login(username='accountuser', password='password123')
        # Switching to someone else's profile returns 404
        res_switch = self.client.get(f'/accounts/profiles/{other_profile.id}/switch/')
        self.assertEqual(res_switch.status_code, 404)
        # Deleting someone else's profile returns 404
        res_del = self.client.post(f'/accounts/profiles/{other_profile.id}/delete/')
        self.assertEqual(res_del.status_code, 404)

    def test_unauthenticated_profiles_redirect(self):
        response = self.client.get('/accounts/profiles/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

