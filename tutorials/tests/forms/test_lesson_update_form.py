from django.test import TestCase
from tutorials.forms import LessonUpdateForm
from tutorials.models import Lesson, Language, Student, Tutor
from django.contrib.auth import get_user_model
from django.utils.timezone import now

class LessonUpdateFormTestCase(TestCase):
    def setUp(self):
        # Create a student and a tutor 

        self.user_student = get_user_model().objects.create_user(
            username='@student',
            first_name='Student',
            last_name='One',
            email='student.one@example.com',
            password='password123',
            role='student'
        )
        self.user_tutor = get_user_model().objects.create_user(
            username='@tutor',
            first_name='Tutor',
            last_name='One',
            email='tutor.one@example.com',
            password='password123',
            role='tutor'
        )

        # Create student, tutor, and language instances
        self.student = Student.objects.create(UserID=self.user_student)
        self.tutor = Tutor.objects.create(UserID=self.user_tutor)
        self.language = Language.objects.create(name="Python")

        # Create a lesson
        self.lesson = Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            language=self.language,
            date="2024-12-05",
            time="14:00",
            venue="Room 101",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )

    def test_form_pre_filled_with_original_lesson_data(self):
        """Test that the form is pre-filled with the original lesson details."""

        # Initialise the form with the lesson instance
        form = LessonUpdateForm(instance=self.lesson)

        # Assert that the initial data matches the lesson instance
        self.assertEqual(form.fields['new_date'].initial, self.lesson.date)
        self.assertEqual(form.fields['new_time'].initial, self.lesson.time)

    def test_form_valid_when_cancel_lesson_checked(self):
        """Test if the form is valid when the cancel lesson checkbox is selected."""

        data = {
            'cancel_lesson': True,
            'new_date': '',
            'new_time': ''
        }

        form = LessonUpdateForm(data)

        self.assertTrue(form.is_valid())

    def test_form_invalid_when_cancel_lesson_not_checked_and_no_new_date_or_time(self):
        """Test if the form is invalid when the cancel lesson is not checked and no new date/time is provided."""

        data = {
            'cancel_lesson': False,
            'new_date': '',
            'new_time': ''
        }

        form = LessonUpdateForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ["Both New Date and New Time are required when cancelling is not selected."])

    def test_form_valid_when_cancel_lesson_not_checked_and_new_date_and_time_provided(self):
        """Test if the form is valid when cancel lesson is not checked and new date/time are provided."""

        data = {
            'cancel_lesson': False,
            'new_date': '2024-12-05',
            'new_time': '14:00'
        }

        form = LessonUpdateForm(data)

        self.assertTrue(form.is_valid())

    def test_form_invalid_when_new_date_provided_but_no_new_time(self):
        """Test if the form is invalid when new date is provided but no time is given."""

        data = {
            'cancel_lesson': False,
            'new_date': '2024-12-05',
            'new_time': ''
        }

        form = LessonUpdateForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ["Both New Date and New Time are required when cancelling is not selected."])

    def test_form_invalid_when_new_time_provided_but_no_new_date(self):
        """Test if the form is invalid when new time is provided but no date is given."""

        data = {
            'cancel_lesson': False,
            'new_date': '',
            'new_time': '14:00'
        }

        form = LessonUpdateForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ["Both New Date and New Time are required when cancelling is not selected."])

    def test_form_valid_when_cancel_lesson_checked_and_date_time_provided(self):
        """Test if the form is valid when cancel lesson is checked and date/time are provided."""

        data = {
            'cancel_lesson': True,
            'new_date': '2024-12-05',
            'new_time': '14:00'
        }

        form = LessonUpdateForm(data)

        self.assertTrue(form.is_valid())

    def test_form_valid_with_full_lesson_data(self):
        """Test if the form is valid with all the lesson fields filled, including reschedule."""

        data = {
            'cancel_lesson': False,
            'new_date': '2024-12-10',
            'new_time': '15:00'
        }

        form = LessonUpdateForm(data)

        self.assertTrue(form.is_valid())