from django.test import TestCase
from tutorials.forms import LessonUpdateForm

class LessonUpdateFormTestCase(TestCase):
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