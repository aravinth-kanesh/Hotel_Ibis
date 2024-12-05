from django.test import TestCase
from tutorials.models import StudentRequest, Student, Language, User

class StudentRequestModelTest(TestCase):
    def test_create_request(self):
        """Tests creating a StudentRequest instance with valid data."""
        user = User.objects.create(username="@johndoe", email="johndoe@example.com", role="student")
        student = Student.objects.get(user=user)
        language = Language.objects.create(name="Python")
        request = StudentRequest.objects.create(
            student=student,
            language=language,
            description="Test request",
            time="10:00:00",
            venue="Test Venue",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
        )
        self.assertEqual(request.is_allocated, False)
        self.assertEqual(str(request), f"Request {request.id} by @johndoe for Python")
