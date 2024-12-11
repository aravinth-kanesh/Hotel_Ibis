from django.test import TestCase
from tutorials.forms import StudentRequestProcessingForm
from tutorials.models import Tutor, Language, StudentRequest, Student, User

class StudentRequestProcessingFormTestCase(TestCase):
    def setUp(self):
        """Set up data for the tests."""
        
        # Create Language instance
        self.language_python = Language.objects.create(name="Python")
        
        # Create Student user and Student instance
        self.student_user = User.objects.create_user(
            username='student1',
            password='password123',
            first_name='Student',
            last_name='One',
            email='student1@example.com'
        )
        self.student, _ = Student.objects.get_or_create(UserID=self.student_user)

        # Create Tutor user and Tutor instance
        self.tutor_user_python = User.objects.create_user(
            username='tutor_python',
            password='password123',
            first_name='Python Tutor',
            last_name='One',
            email='python_tutor@example.com'
        )
        self.tutor_python, _ = Tutor.objects.get_or_create(UserID=self.tutor_user_python)
        self.tutor_python.languages.add(self.language_python)

        # Create a student request instance (request for Python tutor)
        self.student_request = StudentRequest.objects.create(
            student=self.student,
            language=self.language_python, 
            description="Looking for Python tutor",
            time='14:30:00',
            venue="Room 101",
            duration=60,
            frequency='once a week',
            term='sept-christmas'
        )

        # Valid test data
        self.valid_date = '2024-12-15' 
        self.valid_time = '14:30:00' 
    
    def test_form_valid_with_correct_language(self):
        """Test if the form is valid when the tutor teaches the requested language."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor_python,  
            'first_lesson_date': '2024-12-15',
            'first_lesson_time': '14:30:00',
        }

        form = StudentRequestProcessingForm(data, instance=self.student_request)

        self.assertTrue(form.is_valid())  

    def test_form_valid_with_all_fields(self):
        """Test if the form is valid with all required fields provided."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor_python,
            'first_lesson_date': self.valid_date,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'accepted')
        self.assertEqual(form.cleaned_data['details'], '')
        self.assertEqual(form.cleaned_data['tutor'], self.tutor_python)
        self.assertEqual(str(form.cleaned_data['first_lesson_date']), self.valid_date)
        self.assertEqual(str(form.cleaned_data['first_lesson_time']), self.valid_time)

    def test_form_invalid_without_first_lesson_date(self):
        """Test if the form is invalid when no first lesson date is provided."""
        
        data = {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor_python,
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
            'tutor': self.tutor_python,
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
        }

        form = StudentRequestProcessingForm(data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'denied')
        self.assertEqual(form.cleaned_data['details'], 'Scheduling conflict')

    def test_form_invalid_without_tutor(self):
        """Test if the form is invalid when status is 'accepted' but tutor is missing."""
        
        data = {
            'status': 'accepted',
            'first_lesson_date': self.valid_date,
            'first_lesson_time': self.valid_time
        }

        form = StudentRequestProcessingForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn('tutor', form.errors)