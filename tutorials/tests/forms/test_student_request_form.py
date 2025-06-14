from django.test import TestCase
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

    def test_invalid_duration_zero(self):
        """Test that a duration of zero is invalid."""
        data = {
            "language": self.language.id,
            "description": "Need help with Python.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 0,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("duration", form.errors)

    def test_invalid_duration_negative(self):
        """Test that a negative duration is invalid."""
        data = {
            "language": self.language.id,
            "description": "Need help with Python.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": -30,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("duration", form.errors)

    def test_clean_method_missing_language(self):
        """Test that missing language raises an error."""
        data = {
            "description": "Need help with Python.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 60,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("language", form.errors)

    def test_clean_method_missing_description(self):
        """Test that missing description raises an error."""
        data = {
            "language": self.language.id,
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 60,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_clean_method_missing_required_fields(self):
        """Test that missing any required field raises an error."""
        data = {
            "language": self.language.id,
            "description": "Need help with Python.",
            "duration": 60,
            "frequency": "once a week",
        }
        form = StudentRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)
        self.assertIn("time", form.errors)
        self.assertIn("venue", form.errors)
        self.assertIn("term", form.errors)

    def test_valid_form_with_all_fields(self):
        """Test that the form is valid when all fields are filled."""
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