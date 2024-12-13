from django.test import TestCase
from django.utils.timezone import now
from tutorials.models import StudentRequest, Student, Language, User
from tutorials.forms import StudentRequestForm

class StudentRequestFormTests(TestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            password='password123',
            first_name='Student',
            last_name='One',
            email='student1@example.com'
        )
        self.student, _ = Student.objects.get_or_create(UserID=self.student_user)
        self.language = Language.objects.create(name="Python")

    def test_valid_form(self):
        """Test that a valid form is processed correctly."""
        data = {
            "language": self.language.id,
            "description": "Need help with Python.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 90,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing."""
        data = {
            "description": "Need help with Python.",
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("language", form.errors)
        self.assertIn("date", form.errors)
        self.assertIn("time", form.errors)
        self.assertIn("venue", form.errors)
        self.assertIn("duration", form.errors)
        self.assertIn("frequency", form.errors)
        self.assertIn("term", form.errors)

    def test_invalid_duration(self):
        """Test that a duration less than or equal to zero is invalid."""
        form_data = {
            "language": self.language.id,
            "description": "Need help with Python.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 0,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=form_data)
        form.full_clean()

  
        self.assertFalse(form.is_valid())
        self.assertIn("duration", form.errors)
        
    def test_clean_method_errors(self):
        """Test that the custom clean method handles missing fields correctly."""
        form_data = {}
        form = StudentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("language", form.errors)
        self.assertIn("description", form.errors)

    def test_widget_attributes(self):
        """Test that the widgets have the correct attributes."""
        form = StudentRequestForm()
        self.assertEqual(form.fields['description'].widget.attrs['placeholder'], "Enter any other requirements here.")
        self.assertEqual(form.fields['venue'].widget.attrs['placeholder'], "Enter venue address")
        self.assertEqual(form.fields['duration'].widget.attrs['placeholder'], "Enter number of minutes")
        rendered = form.as_p()
        self.assertIn('type="date"', rendered)  
        self.assertIn('Enter any other requirements here.', rendered)
        self.assertIn('Enter venue address', rendered)
