from django.test import TestCase
from tutorials.forms import StudentRequestProcessingForm

class StudentRequestProcessingFormTestCase(TestCase):
    def test_form_valid_when_status_accepted(self):
        """Test if the form is valid when the status is 'accepted' and no details are provided."""

        data = {
            'status': 'accepted',
            'details': ''
        }

        form = StudentRequestProcessingForm(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'accepted')
        self.assertEqual(form.cleaned_data['details'], '')

    def test_form_valid_when_status_accepted_with_details(self):
        """Test if the form is valid when the status is 'accepted' and details are provided."""

        data = {
            'status': 'accepted',
            'details': 'Request accepted'
        }

        form = StudentRequestProcessingForm(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'accepted')
        self.assertEqual(form.cleaned_data['details'], 'Request accepted')

    def test_form_valid_when_status_denied_with_details(self):
        """Test if the form is valid when the status is 'denied' and details are provided."""

        data = {
            'status': 'denied',
            'details': 'Request denied due to schedule conflict.'
        }

        form = StudentRequestProcessingForm(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'denied')
        self.assertEqual(form.cleaned_data['details'], 'Request denied due to schedule conflict.')

    def test_form_invalid_when_status_denied_without_details(self):
        """Test if the form is invalid when the status is 'denied' but no details are provided."""

        data = {
            'status': 'denied',
            'details': ''
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['details'], ['You must provide a reason in the Details field when denying a request.'])

    def test_form_invalid_when_status_empty_with_details(self):
        """Test if the form is invalid when no status is provided."""

        data = {
            'status': '',
            'details': 'Request denied due to scheduling conflict'
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['status'], ['This field is required.'])

    def test_form_invalid_when_status_empty_without_details(self):
        """Test if the form is invalid when status is empty and no details are provided."""

        data = {
            'status': '',
            'details': ''
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['status'], ['This field is required.'])