from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import StudentRequest, Student, Language, User

class StudentRequestListViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']  

    def setUp(self):
        # Load the UserID from the fixture
        self.user = User.objects.get(pk=3)  
        self.student, _ = Student.objects.get_or_create(UserID=self.user)

        # Create test data for StudentRequest
        self.language = Language.objects.create(name="C++")
        self.request1 = StudentRequest.objects.create(
            student=self.student,
            language=self.language,
            description="Request for C++ help.",
            date="2024-12-15",
            time="10:00:00",
            venue="Library",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )
        self.request2 = StudentRequest.objects.create(
            student=self.student,
            language=self.language,
            description="Request for C++ lessons.",
            date="2024-12-15",
            time="14:00:00",
            venue="Classroom 2",
            duration=90,
            frequency="once per fortnight",
            term="jan-easter"
        )

        # For isolation testing
        other_user = User.objects.create_user(
            username="@otheruser",
            password="Password123"
        )
        other_student, _ = Student.objects.get_or_create(UserID=other_user)
        StudentRequest.objects.create(
            student=other_student,
            language=self.language,
            description="Another student's request.",
            date="2024-12-15",
            time="16:00:00",
            venue="Lecture Hall",
            duration=120,
            frequency="once per fortnight",
            term="may-july"
        )

       
        self.client = Client()
        self.client.login(username=self.user.username, password="Password123")

      
        self.url = reverse("view_request")

    def test_redirect_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse(settings.LOGIN_URL)}?next={self.url}")

    def test_list_only_user_requests(self):
        """Test that only the logged-in user's requests are shown."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "student_requests_list.html")
        self.assertEqual(len(response.context["requests"]), 2)
        descriptions = [request.description for request in response.context["requests"]]
        self.assertIn("Request for C++ help.", descriptions)
        self.assertIn("Request for C++ lessons.", descriptions)
        self.assertNotIn("Another student's request.", descriptions)

    def test_no_requests_for_user(self):
        """Test behavior when the logged-in student has no requests."""
        # Log in as a different UserID with no requests
        other_user = User.objects.create_user(
            username="@emptyuser",
            email = "empty@example.com",
            password="emptypassword123"
        )
        self.client.login(username="@emptyuser", password="emptypassword123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No class requests found.")  # Adjust message to match your template
        self.assertEqual(len(response.context["requests"]), 0)

    def test_student_profile_does_not_exist(self):
        """Test behavior when the logged-in UserID is not student."""
        # Create and log in as a UserID without a student profile
        no_profile_user = User.objects.create_user(
            username="@notstudent",
            email = "notstudent@example.com",
            password="notstudent123",
            role = "tutor"
        )
        self.client.login(username="@notstudent", password="notstudent123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["requests"]), 0)
