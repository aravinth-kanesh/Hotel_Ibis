from django.test import TestCase
from tutorials.models import StudentRequest, Student, Language, User

class StudentRequestModelTest(TestCase):
    def test_create_request(self):
        user = User.objects.create(username="@student1", email="student1@example.com", role="student")
        student, _ = Student.objects.get_or_create(UserID=user)
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
        self.assertEqual(str(request), f"Request {request.id} by @student1 for Python")
