from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UsersDirectoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alice',
            password='testpass123',
            email='alice@example.com',
            role='admin',
            direction='design',
        )

    def test_users_directory_requires_auth(self):
        response = self.client.get(reverse('users_list'))
        self.assertEqual(response.status_code, 302)

    def test_users_directory_renders_for_authenticated_user(self):
        self.client.login(username='alice', password='testpass123')
        response = self.client.get(reverse('users_list'))
        self.assertEqual(response.status_code, 200)
