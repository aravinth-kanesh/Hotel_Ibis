"""Tests of the log out view."""
from django.test import TestCase
from django.urls import reverse
from tutorials.models import User
from tutorials.tests.helpers import LogInTester

class LogOutViewTestCase(TestCase, LogInTester):
    """Tests of the log out view."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Initialises the URL for log out and gets a test user."""
        self.url = reverse('log_out')
        self.user = User.objects.get(username='@johndoe')

    def test_log_out_url(self):
        """Tests if the log out URL is correctly resolved to '/log_out/'."""
        self.assertEqual(self.url,'/log_out/')

    def test_get_log_out(self):
        """Tests get request to the log out page, ensuring the user is logged out and redirects to the home page."""
        self.client.login(username='@johndoe', password='Password123')
        self.assertTrue(self._is_logged_in())
        response = self.client.get(self.url, follow=True)
        response_url = reverse('home')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertFalse(self._is_logged_in())

    def test_get_log_out_without_being_logged_in(self):
        """Tests get request to the log out page when the user is not logged in and redirects to the home page."""
        response = self.client.get(self.url, follow=True)
        response_url = reverse('home')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertFalse(self._is_logged_in())