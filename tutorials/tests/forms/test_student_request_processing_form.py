from django.test import TestCase
from tutorials.forms import StudentRequestProcessingForm
from tutorials.models import Tutor, Language
from django.contrib.auth import get_user_model

class StudentRequestProcessingFormTestCase(TestCase):
    def setUp(self):
        """Set up data for the tests."""
        
        # Create Language instance
        self.language = Language.objects.create(name="Spanish")
        
        # Create a user for the tutor
        self.tutor_user = get_user_model().objects.create_user(
            username='tutor1',
            password='password123',
            first_name='Tutor',
            last_name='One',
            email='tutor1@example.com'
        )

        # Create Tutor instance linked to the user
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)
        self.tutor.languages.add(self.language)
        
        # Create fixed date and time for valid test cases
        self.valid_date = '2024-12-15'  # Fixed future date
        self.valid_time = '14:30:00'    # Fixed future time

    def test_form_valid_with_all_fields(self):
        """Test if the form is valid with all required fields provided."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor,
            'first_lesson_date': self.valid_date,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)

        # Print form errors if validation fails (useful for debugging)
        if not form.is_valid():
            print(form.errors)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'accepted')
        self.assertEqual(form.cleaned_data['details'], '')
        self.assertEqual(form.cleaned_data['tutor'], self.tutor)
        self.assertEqual(str(form.cleaned_data['first_lesson_date']), self.valid_date)
        self.assertEqual(str(form.cleaned_data['first_lesson_time']), self.valid_time)

    def test_form_invalid_without_tutor(self):
        """Test if the form is invalid when no tutor is selected."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'first_lesson_date': self.valid_date,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn('tutor', form.errors)
        self.assertIn('This field is required.', form.errors['tutor'])
        self.assertIn('You must select a tutor for accepted requests.', form.errors['tutor'])

    def test_form_invalid_without_first_lesson_date(self):
        """Test if the form is invalid when no first lesson date is provided."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['first_lesson_date'], ['You must provide the first lesson date.'])

    def test_form_invalid_without_first_lesson_time(self):
        """Test if the form is invalid when no first lesson time is provided."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor,
            'first_lesson_date': self.valid_date
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['first_lesson_time'], ['You must provide the first lesson time.'])

    def test_form_valid_with_status_denied_and_no_tutor_or_lesson_time(self):
        """Test if the form is valid when status is 'denied' and no tutor or lesson date/time are provided."""
        
        data = {
            'status': 'denied',
            'details': 'Scheduling conflict',
            'tutor': self.tutor,
            'first_lesson_date': self.valid_date,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)

        # Print form errors if validation fails (useful for debugging)
        if not form.is_valid():
            print(form.errors)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'denied')
        self.assertEqual(form.cleaned_data['details'], 'Scheduling conflict')

    def test_form_invalid_with_status_accepted_and_missing_fields(self):
        """Test if the form is invalid when status is 'accepted' but tutor, date, or time are missing."""
        
        data = {
            'status': 'accepted',
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn('tutor', form.errors)
        self.assertIn('first_lesson_date', form.errors)
        self.assertIn('first_lesson_time', form.errors)