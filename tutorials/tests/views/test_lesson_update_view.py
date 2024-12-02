from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Lesson, Tutor, Student, Language

#Test commit

class LessonUpdateViewTestCase(TestCase):
    """Test suite for the LessonUpdateView where the admin user performs the actions."""

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

        # Create a lesson instance
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