"""Tests of the home view."""
from django.test import TestCase
from django.urls import reverse
from tutorials.models import User

class HomeViewTestCase(TestCase):
    """Tests of the home view."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets up test variables, like the URL and user."""
        self.url = reverse('home')
        self.user = User.objects.get(username='@johndoe')

    def test_home_url(self):
        """Tests that the home page URL is correct."""
        self.assertEqual(self.url,'/')

    def test_get_home(self):
        """Tests that the home page returns a successful response."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_get_home_redirects_when_logged_in(self):
        """Tests that once users have logged in, they are redirected to the dashboard."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')