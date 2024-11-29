from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import StudentRequest, Tutor, Student, Language, Lesson
from django.utils import timezone

class StudentRequestProcessingViewTestCase(TestCase):
    """Test suite for the StudentRequestProcessingView where the admin user processes student requests."""

    def setUp(self):
        # Create an admin 
        self.user_admin = get_user_model().objects.create_user(
            username='@admin_user',
            first_name='Admin',
            last_name='User',
            email='admin.user@example.com',
            password='adminpassword',
            role='admin'  
        )

        # Create a tutor 
        self.user_tutor = get_user_model().objects.create_user(
            username='@john_doe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            password='password123',
            role='tutor'
        )

        # Create a student 
        self.user_student = get_user_model().objects.create_user(
            username='@jane_smith',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            password='password123',
            role='student'
        )

        # Create a language
        self.language = Language.objects.create(name="Python")

        # Create tutor and student instances
        self.tutor = Tutor.objects.create(UserID=self.user_tutor)
        self.student = Student.objects.create(UserID=self.user_student)

        # Create a student request
        self.student_request = StudentRequest.objects.create(
            student=self.student,
            language=self.language,
            description="Looking for a tutor for Python",
            is_allocated=False,
            time="10:00",
            venue="BH 6.02",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )

    def test_admin_can_access_student_request_processing_form(self):
        """Test that the admin can access the student request processing form."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Get the URL for processing the student request
        response = self.client.get(reverse('process_request', args=[self.student_request.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'process_request.html')

    def test_accept_student_request(self):
        """Test that accepting a student request creates a new lesson."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Accept the request by posting with status 'accepted'
        self.client.post(reverse('process_request', args=[self.student_request.id]), {
            'status': 'accepted',
            'details': '',  # No details needed for accepted requests
        })

        # Check if the lesson was created
        lesson = Lesson.objects.first()
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson.student, self.student)
        self.assertEqual(lesson.language, self.language)
        self.assertEqual(lesson.time, timezone.datetime.strptime("10:00", "%H:%M").time())
        self.assertEqual(lesson.date, timezone.datetime.strptime("2024-12-01", "%Y-%m-%d").date())

        # Ensure the request is now marked as 'accepted'
        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.is_allocated, True)

    def test_reject_student_request(self):
        """Test that rejecting a student request does not create a lesson."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Reject the request by posting with status 'denied'
        self.client.post(reverse('process_request', args=[self.student_request.id]), {
            'status': 'denied',
            'details': 'The student is unavailable at the requested time.',
        })

        # Check that no lesson was created
        lesson = Lesson.objects.filter(student=self.student, tutor=self.tutor).first()
        self.assertIsNone(lesson)

        # Ensure the request is now marked as 'denied'
        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.is_allocated, False)