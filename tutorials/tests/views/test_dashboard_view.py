"""Tests of the dashboard view."""
from django.test import TestCase
from django.urls import reverse
from tutorials.models import User

class DashboardViewTestCase(TestCase):
    """Tests of the dashboard view."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets the URL and gets user objects for an admin, tutor, and student."""
        self.url = reverse('dashboard')
        self.user_admin = User.objects.get(username='@adminuser')
        self.user_tutor = User.objects.get(username='@tutoruser')
        self.user_student = User.objects.get(username='@studentuser')

    def test_dashboard_url(self):
        """Ensure the URL is set to /dashboard/."""
        self.assertEqual(self.url, '/dashboard/')

    def test_get_dashboard_redirects_when_not_logged_in(self):
        """Ensure a user is redirected to login if they are not logged in."""
        response = self.client.get(self.url, follow=True)
        login_url = reverse('log_in')
        self.assertRedirects(response, login_url, status_code=302, target_status_code=200)

    def test_get_dashboard_for_admin(self):
        """Ensure that admin can access the dashboard."""
        self.client.login(username=self.user_admin.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Send Message')
        self.assertContains(response, 'View Messages')

    def test_get_dashboard_for_tutor(self):
        """Ensure that tutors can access the dashboard."""
        self.client.login(username=self.user_tutor.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Manage Languages')
        self.assertContains(response, 'Send Message')

    def test_get_dashboard_for_student(self):
        """Ensure that students can access the dashboard."""
        self.client.login(username=self.user_student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Request Lesson')
        self.assertContains(response, 'View Requests')

    def test_get_dashboard_for_unrecognized_role(self):
        """Ensures that an unrecognised role returns an error message."""
        user_unknown = User.objects.create_user(username='@unknownuser', password="Password123", role="unknown")
        self.client.login(username=user_unknown.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your role is not recognized.')

    def test_dashboard_redirects_to_dashboard_when_logged_in(self):
        """Ensure that users that have logged in are redirected to the dashboard from home."""
        self.client.login(username=self.user_student.username, password="Password123")
        home_url = reverse('home')
        response = self.client.get(home_url, follow=True)
        self.assertRedirects(response, self.url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
