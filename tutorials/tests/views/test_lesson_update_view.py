from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Lesson, Tutor, Student, Language, TutorAvailability

class LessonUpdateViewTestCase(TestCase):
    """Test suite for the LessonUpdateView where the admin user performs the actions."""

    def setUp(self):
        self.create_users()
        self.create_language_and_associations()
        self.create_lesson_and_availabilities()

    def create_users(self):
        """Create users for admin, tutor, and student."""
        User = get_user_model()
        self.user_admin = User.objects.create_user(
            username='@admin_user',
            first_name='Admin',
            last_name='User',
            email='admin.user@example.com',
            password='adminpassword',
            role='admin' 
        )

        self.user_tutor = User.objects.create_user(
            username='@john_doe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            password='password123',
            role='tutor'
        )

        self.user_student = User.objects.create_user(
            username='@jane_smith',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            password='password123',
            role='student'
        )

    def create_language_and_associations(self):
        """Create a language and associate it with the tutor."""
        self.language = Language.objects.create(name="Python")
        self.tutor, _ = Tutor.objects.get_or_create(UserID=self.user_tutor)
        self.student, _ = Student.objects.get_or_create(UserID=self.user_student)
        self.tutor.languages.add(self.language)

    def create_lesson_and_availabilities(self):
        """Create a lesson and related tutor availability."""
        self.lesson = Lesson.objects.create(
            tutor=self.tutor,
            student=self.student,
            language=self.language,
            time="10:00",
            date="2024-12-01",
            venue="BH 6.02",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )

        availability_data = [
            {"day": self.lesson.date, "start_time": "09:00", "end_time": "17:00"},
            {"day": "2024-12-05", "start_time": "09:00", "end_time": "17:00"},
        ]

        for data in availability_data:
            TutorAvailability.objects.create(
                tutor=self.tutor,
                start_time=data["start_time"],
                end_time=data["end_time"],
                day=data["day"],
                availability_status='available',
                action='edit'
            )

    def test_admin_can_access_lesson_update_form(self):
        """Test that the admin can access the lesson update form."""

        self.client.login(username='@admin_user', password='adminpassword')

        response = self.client.get(reverse('lesson_update', args=[self.lesson.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lesson_update.html')

    def test_cancel_lesson(self):
        """Test that the admin can cancel a lesson and the database is correctly updated."""

        self.client.login(username='@admin_user', password='adminpassword')

        self.client.post(reverse('lesson_update', args=[self.lesson.id]), {
            'cancel_lesson': True
        })

        # Verify that the lesson is deleted
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_reschedule_lesson(self):
        """Test that the admin can reschedule a lesson and the database is correctly updated."""

        self.client.login(username='@admin_user', password='adminpassword')

        self.client.post(reverse('lesson_update', args=[self.lesson.id]), {
            'cancel_lesson': False,
            'new_date': '2024-12-05',
            'new_time': '14:00'
        })

        # Fetch the updated lesson and check the changes
        updated_lesson = Lesson.objects.get(id=self.lesson.id)

        self.assertEqual(str(updated_lesson.date), "2024-12-05")
        self.assertEqual(str(updated_lesson.time), "14:00:00")

    def test_invalid_form_submission(self):
        """Test that submitting invalid data results in a form error."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Simulate a POST request with invalid data
        response = self.client.post(reverse('lesson_update', args=[self.lesson.id]), {
            'cancel_lesson': False,            
            'new_date': 'invalid_date',        
            'new_time': 'invalid_time',        
        })

        # Check that the form is rendered again, meaning validation failed
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lesson_update.html')