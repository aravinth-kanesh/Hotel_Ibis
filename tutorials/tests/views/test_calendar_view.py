from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date
from tutorials.models import Student, Lesson
from tutorials.views import next_month, prev_month
from django.contrib.auth import get_user_model

class CalendarViewTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create_user(
            username='@testuser',
            email='testuser@example.com',
            password='password123',
            role='tutor',
        )
        self.calendar_url = reverse('calendar')

    def test_calendar_view_requires_login(self):
        """Calendar view should redirect to login if user is not authenticated."""
        response = self.client.get(self.calendar_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"/log_in/?next=/calendar/")


    def test_calendar_view_no_student_profile_redirects(self):
        """If the user doesn't have a student profile, they are redirected."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.calendar_url)
        # Assuming 'dashboard' is the name of the redirect URL if no student found
        self.assertRedirects(response, reverse('dashboard'))

    def test_calendar_view_with_student_and_lessons(self):
        """If the student and lessons exist, the calendar view should render properly."""
        # Create the student profile
        student = Student.objects.create(UserID=self.user)

        # Create some lessons in the current month/year
        current_year = date.today().year
        current_month = date.today().month
        Lesson.objects.create(student=student, date=date(current_year, current_month, 10))
        Lesson.objects.create(student=student, date=date(current_year, current_month, 15))

        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.calendar_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        # Check that the calendar HTML is in the response
        self.assertIn('calendar', response.context)
        # Check for lessons dates present in the calendar HTML
        self.assertIn('10', response.content.decode('utf-8'))
        self.assertIn('15', response.content.decode('utf-8'))

    def test_calendar_view_with_year_month_parameters(self):
        """Test the view with explicit year and month parameters."""
        student = Student.objects.create(UserID=self.user)

        year = 2024
        month = 12
        Lesson.objects.create(student=student, date=date(year, month, 25))

        self.client.login(username='testuser', password='password123')
        url = reverse('calendar/<int:year>/<int:month>/', args=[year, month])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        # Check that the calendar is for the specified year/month
        self.assertIn(str(year), response.content.decode('utf-8'))
        self.assertIn('December', response.content.decode('utf-8'))
        # Check that the lesson date is present
        self.assertIn('25', response.content.decode('utf-8'))

    def test_next_month(self):
        """Test the next_month utility function."""
        # If it's December
        result = next_month(2024, 12)
        self.assertEqual(result, {'year': 2025, 'month': 1})

        # If it's not December
        result = next_month(2024, 11)
        self.assertEqual(result, {'year': 2024, 'month': 12})

    def test_prev_month(self):
        """Test the prev_month utility function."""
        # If it's January
        result = prev_month(2024, 1)
        self.assertEqual(result, {'year': 2023, 'month': 12})

        # If it's not January
        result = prev_month(2024, 5)
        self.assertEqual(result, {'year': 2024, 'month': 4})
