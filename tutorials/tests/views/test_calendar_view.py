from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from tutorials.models import Student, Lesson, Tutor, Language
from tutorials.views import next_month, prev_month

User = get_user_model()

class CalendarViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data for the entire TestCase. This method is run once for the TestCase.
        """
        cls.tutor_user = User.objects.create_user(
            username='@tutoruser',
            email='tutor@example.com',
            password='tutorpass',
            role='tutor'
        )

        cls.tutor = Tutor.objects.get(UserID=cls.tutor_user)


        cls.language = Language.objects.create(name='english')


        cls.student_user = User.objects.create_user(
            username='@studentuser',
            email='student@example.com',
            password='studentpass',
            role='student'
        )

        cls.student = Student.objects.get(UserID=cls.student_user)


        cls.admin_user = User.objects.create_user(
            username='@adminuser',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )


        cls.calendar_url = reverse('calendar')
        cls.dashboard_url = reverse('dashboard')

    def setUp(self):
        """
        Set up a fresh Client instance for each test method.
        """
        self.client = Client()

    def test_calendar_view_requires_login(self):
        """
        Calendar view should redirect to login if user is not authenticated.
        """
        response = self.client.get(self.calendar_url)
        self.assertNotEqual(response.status_code, 200)

        self.assertRedirects(response, f'/log_in/?next={self.calendar_url}')

    def test_calendar_view_no_student_profile_redirects(self):
        """
        If the user doesn't have a student profile, they are redirected to the dashboard.
        """

        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.calendar_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_calendar_view_with_student_and_lessons(self):
        """
        If the student and lessons exist, the calendar view should render properly.
        """

        current_year = date.today().year
        current_month = date.today().month

        Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            language=self.language,
            date=date(current_year, current_month, 10),
            price=50.00
        )
        Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            language=self.language,
            date=date(current_year, current_month, 15),
            price=50.00
        )

        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.calendar_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertIn('calendar', response.context)

        content = response.content.decode('utf-8')
        self.assertIn('10', content)
        self.assertIn('15', content)

    def test_calendar_view_with_year_month_parameters(self):
        """
        Test the view with explicit year and month parameters.
        """
        specific_year = 2024
        specific_month = 12
        Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            language=self.language,
            date=date(specific_year, specific_month, 25),
            price=50.00
        )


        self.client.login(username='@studentuser', password='studentpass')
        url = reverse('calendar', args=[specific_year, specific_month])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertIn('calendar', response.context)

        content = response.content.decode('utf-8')

        self.assertIn(str(specific_year), content)
        self.assertIn('December', content)

        self.assertIn('25', content)

    def test_next_month(self):
        """
        Test the next_month utility function.
        """
        result = next_month(2024, 12)
        self.assertEqual(result, {'year': 2025, 'month': 1})

        result = next_month(2024, 11)
        self.assertEqual(result, {'year': 2024, 'month': 12})

    def test_prev_month(self):
        """
        Test the prev_month utility function.
        """
        result = prev_month(2024, 1)
        self.assertEqual(result, {'year': 2023, 'month': 12})

        result = prev_month(2024, 5)
        self.assertEqual(result, {'year': 2024, 'month': 4})
