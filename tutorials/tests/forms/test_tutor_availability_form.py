from datetime import date, time, timedelta
from django import forms
from django.test import TestCase
from tutorials.models import Tutor, User, TutorAvailability
from tutorials.forms import TutorAvailabilityForm
from unittest.mock import patch
from tutorials.term_dates import get_term

class TutorAvailabilityFormTestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)

        self.form_input = {
            'tutor':self.tutor.id,
            'day': '2024-12-14',
            'start_time': '10:00',
            'end_time': '12:00',
            'availability_status': 'available',
            'repeat': 'once',
        }

    def test_form_has_necessary_fields(self):
        form = TutorAvailabilityForm()
        self.assertIn('tutor', form.fields)
        self.assertIn('day', form.fields)
        date_field = form.fields['end_time']
        self.assertTrue(isinstance(date_field, forms.TimeField))
        self.assertIn('start_time', form.fields)
        start_time_field = form.fields['start_time']
        self.assertTrue(isinstance(start_time_field, forms.TimeField))
        self.assertIn('end_time', form.fields)
        end_time_field = form.fields['end_time']
        self.assertTrue(isinstance(end_time_field, forms.TimeField))
        self.assertIn('availability_status', form.fields)
        self.assertIn('repeat', form.fields)

    def test_valid_form(self):
        form = TutorAvailabilityForm(data = self.form_input)
        self.assertTrue(form.is_valid())

    def test_invalid_form_blank_tutor(self):
        self.form_input['tutor'] = " "
        form = TutorAvailabilityForm(data = self.form_input)
        self.assertFalse(form.is_valid())

    def test_invalid_form_blank_tutor(self):
        self.form_input['tutor'] = " "
        form = TutorAvailabilityForm(data = self.form_input)
        self.assertFalse(form.is_valid())

    def test_invalid_form_blank_date(self):
        self.form_input['day'] = " "
        form = TutorAvailabilityForm(data = self.form_input)
        self.assertFalse(form.is_valid())

    def test_valid_form_can_be_saved(self):
        form = TutorAvailabilityForm(data = self.form_input)
        before_count = TutorAvailability.objects.count()
        form.save()
        after_count = TutorAvailability.objects.count()
        self.assertEquals(before_count+1, after_count)

    def test_start_time_after_end_time(self):
        form = TutorAvailabilityForm(data={
            'tutor': self.tutor.id,
            'day': '2024-12-14',
            'start_time': '11:00',
            'end_time': '10:00',
            'availability_status': 'available',
            'repeat': 'once'
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Start time must be earlier than end time.", form.errors['__all__'])
        form = TutorAvailabilityForm(data=form)

    def test_repeat_weekly_save(self):
        form = TutorAvailabilityForm(data={
            'tutor': self.tutor.id,
            'day': date.today(),
            'start_time': '09:00',
            'end_time': '10:00',
            'availability_status': 'available',
            'repeat': 'weekly'
        })
        if form.is_valid():
            instance = form.save()
            self.assertEqual(TutorAvailability.objects.count(), 1)
            self.assertNotEqual(TutorAvailability.objects.filter(day=date.today() + timedelta(days=7)).count(), 0)

    @patch('tutorials.term_dates.get_term')  # Correct the import path according to your project structure
    def test_not_in_term_time(self, mock_get_term):
        # Set the mock to return controlled term dates
        mock_get_term.return_value = {
            'start_date': date.today() + timedelta(days=30),  # Start date 30 days from today
            'end_date': date.today() + timedelta(days=60)  # End date 60 days from today
        }
        
        # Form data where day is today, outside the mocked term dates
        form_data = {
            'tutor': self.tutor.id,
            'day': date.today().isoformat(),
            'start_time': '10:00',
            'end_time': '12:00',
            'availability_status': 'available',
            'repeat': 'weekly'  # Test with 'weekly' or 'biweekly'
        }
        form = TutorAvailabilityForm(data=form_data)
        self.assertTrue(form.is_valid())  # Ensure other validations pass

        # Testing the save method, expecting a ValueError
        with self.assertRaises(ValueError) as context:
            form.save()

        self.assertEqual(str(context.exception), "Not in term time.")

    def test_save_without_valid_tutor_instance(self):
        form_data = {
            'tutor': 99,
            'day': '2023-01-01',
            'start_time': '09:00',
            'end_time': '10:00',
            'availability_status': 'available',  # Assuming this field is correct
            'repeat': 'once'
        }
        form = TutorAvailabilityForm(data=form_data)
        
        # Ensure the form appears valid to Django, but the tutor is actually not existent
        
        # Try to save and catch the expected ValueError
        with self.assertRaises(ValueError) as context:
            form.save()
        
        self.assertEqual(str(context.exception), "The TutorAvailability could not be created because the data didn't validate.")
        



    

    


    

    
    


