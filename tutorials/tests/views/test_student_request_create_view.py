from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import StudentRequest, Language, Student
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from datetime import date, datetime, timedelta, time


class StudentRequestCreateViewTests(TestCase):
    fixtures = [
        'tutorials/tests/fixtures/other_users.json'
    ]
    def setUp(self):
        # Load the user from the fixture
        self.user = get_user_model().objects.get(pk=3)
        self.assertTrue(hasattr(self.user, 'student_profile'))

        
        # Create a Language instance for the test
        self.language = Language.objects.create(name="Python")
        
        # Log in as the user
        self.client = Client()
        self.client.login(username="@petrapickles", password="Password123")
        

        self.url = reverse("create_request")

    def test_get_request_form(self):
        """Test the form renders correctly for logged-in users."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "student_request_form.html")

    def test_redirect_if_not_logged_in(self):
        """Test that the view redirects non-logged-in users to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {
            "language": self.language.id,
            "description": "I need help.",
            "date": date(2025,1,10),
            "time": time(10,30),
            "venue": "Library Room 2",
            "duration": 60,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse("view_request"))  
        self.assertTrue(StudentRequest.objects.filter(description="I need help.").exists())

    def test_form_submission_invalid(self):
        """Test form submission with invalid data."""
        data = {
            "language": "",  
            "description": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200) 
        self.assertIn("form", response.context)
        form = response.context.get("form")
        self.assertIsNotNone(form)

        self.assertIn("language", form.errors)
        self.assertIn("description", form.errors)
        self.assertIn("date", form.errors)
        self.assertIn("time", form.errors)
        self.assertIn("venue", form.errors)
        self.assertIn("duration", form.errors)
        self.assertIn("frequency", form.errors)
        self.assertIn("term", form.errors)
        self.assertEqual(form.errors["language"], ["This field is required."])
        self.assertEqual(form.errors["description"], ["This field is required."])

    def test_student_assignment_to_request(self):
        """Test that the logged-in student is correctly assigned to the request."""
        data = {
            "language": self.language.id,
            "description": "I want to improve.",
            "date": "2025-01-10",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 90,
            "frequency": "once per fortnight",
            "term": "jan-easter"
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_request"))
        request = StudentRequest.objects.get(description="I want to improve.")
        self.assertEqual(request.student, self.user.student_profile)
        self.assertEqual(request.created_at.date(), now().date())
