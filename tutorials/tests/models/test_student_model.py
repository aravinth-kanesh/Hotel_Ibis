from django.test import TestCase
from tutorials.models import User, Student
from django.db import IntegrityError

class StudentModelTestCase(TestCase):
    """Unit tests for the Student model."""

    def setUp(self):
        self.user = User.objects.create(
            username='@teststudent',
            first_name='Test',
            last_name='Student',
            email='teststudent@example.com',
        )
        self.student, _ = Student.objects.get_or_create(UserID=self.user)

    def test_student_creation(self):
        """Test that a student can be created with a valid user."""
        self.assertEqual(self.student.UserID.username, '@teststudent')
        self.assertEqual(self.student.UserID.first_name, 'Test')
        self.assertEqual(self.student.UserID.last_name, 'Student')
        self.assertEqual(self.student.UserID.email, 'teststudent@example.com')

    def test_student_str_method(self):
        """Test the __str__ method of the Student model."""
        expected_str = f"Student: {self.user.username}"
        self.assertEqual(str(self.student), expected_str)

    def test_user_association(self):
        """Test that the user is correctly associated with the student."""
        self.assertEqual(self.student.UserID, self.user)

    def test_student_unique_user(self):
        """Test that a user can only be associated with one student."""
        # Try creating a new student with the same user
        with self.assertRaises(IntegrityError):
            Student.objects.create(UserID=self.user)