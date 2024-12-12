from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import StudentRequest, Language, Student
from django.utils.timezone import now
from django.contrib.auth import get_user_model

class StudentRequestCreateViewTests(TestCase):
    fixtures = [
        'tutorials/tests/fixtures/other_users.json'
    ]
    def setUp(self):
        # Load the user from the fixture
        self.user = get_user_model().objects.get(pk=3)
        
        # Create a Language instance for the test
        self.language = Language.objects.create(name="Python")
        
        # Log in as the user
        self.client = Client()
        self.client.login(username="@petrapickles", password="Password123")
        
        # Set the URL for the view
        self.url = reverse("student_request_create")

    def test_get_request_form(self):
        """Test the form renders correctly for logged-in users."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "student_request_form.html")

    def test_redirect_if_not_logged_in(self):
        """Test that the view redirects non-logged-in users to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {
            "language": self.language.id,
            "description": "I need help.",
            "time": "10:30:00",
            "venue": "Library Room 2",
            "duration": 60,
            "frequency": "once a week",
            "term": "sept-christmas"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Expect a redirect on success
        self.assertRedirects(response, reverse("my_requests"))  # Ensure it redirects to the success URL
        self.assertTrue(StudentRequest.objects.filter(description="I need help with Spanish grammar.").exists())

    def test_form_submission_invalid(self):
        """Test form submission with invalid data."""
        data = {
            "language": "",  # Missing required field
            "description": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Stays on the same page
        self.assertFormError(response, "form", "language", "This field is required.")
        self.assertFormError(response, "form", "description", "This field is required.")

    def test_student_assignment_to_request(self):
        """Test that the logged-in student is correctly assigned to the request."""
        data = {
            "language": self.language.id,
            "description": "I want to improve.",
            "time": "14:00:00",
            "venue": "Room 1",
            "duration": 90,
            "frequency": "once per fortnight",
            "term": "jan-easter"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        request = StudentRequest.objects.get(description="I want to improve.")
        self.assertEqual(request.student, self.user)
        self.assertEqual(request.created_at.date(), now().date())
