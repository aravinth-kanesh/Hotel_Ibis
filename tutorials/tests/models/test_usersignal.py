from django.test import TestCase
from tutorials.models import Student, Tutor, User

class UserRoleSignalTest(TestCase):
    def test_create_student_profile(self):
        """Tests that a student user creates a student profile."""
        user = User.objects.create(username="@johndoe", email="johndoe@example.com", role="student")
        self.assertTrue(Student.objects.filter(user=user).exists())

    def test_create_tutor_profile(self):
        """Tests that a tutor user creates a tutor profile."""
        user = User.objects.create(username="@janedoe", email="janedoe@example.com", role="tutor")
        self.assertTrue(Tutor.objects.filter(user=user).exists())
