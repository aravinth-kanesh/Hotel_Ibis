from django.test import TestCase
from tutorials.models import Student, Tutor, User

class UserRoleSignalTest(TestCase):
    def setUp(self):
        self.student_role = "student"
        self.tutor_role = "tutor"
        self.admin_role = "admin"

    def test_create_student_profile(self):
        user = User.objects.create(username="@petrapickles", email="petrapickles@example.com", role=self.student_role)
        self.assertTrue(Student.objects.filter(UserID=user).exists())
        self.assertFalse(Tutor.objects.filter(UserID=user).exists())

    def test_create_tutor_profile(self):
        user = User.objects.create(username="@janedoe", email="janedoe@example.com", role=self.tutor_role)
        self.assertTrue(Tutor.objects.filter(UserID=user).exists())
        self.assertFalse(Student.objects.filter(UserID=user).exists())

    def test_switch_student_to_tutor(self):
        user = User.objects.create(username="@petrapickles", email="petrapickles@example.com", role=self.student_role)
        self.assertTrue(Student.objects.filter(UserID=user).exists())
        self.assertFalse(Tutor.objects.filter(UserID=user).exists())

        user.role = self.tutor_role
        user.save()
        self.assertTrue(Tutor.objects.filter(UserID=user).exists())
        self.assertFalse(Student.objects.filter(UserID=user).exists())

    def test_switch_tutor_to_student(self):
        user = User.objects.create(username="@janedoe", email="janedoe@example.com", role=self.tutor_role)
        self.assertTrue(Tutor.objects.filter(UserID=user).exists())
        self.assertFalse(Student.objects.filter(UserID=user).exists())

        user.role = self.student_role
        user.save()
        self.assertTrue(Student.objects.filter(UserID=user).exists())
        self.assertFalse(Tutor.objects.filter(UserID=user).exists())

    def test_role_set_to_admin(self):
        user = User.objects.create(username="@adminuser", email="adminuser@example.com", role="admin")
        self.assertFalse(Student.objects.filter(UserID=user).exists())
        self.assertFalse(Tutor.objects.filter(UserID=user).exists())

        user.role = self.student_role
        user.save()
        self.assertTrue(Student.objects.filter(UserID=user).exists())

        user.role = self.admin_role
        user.save()
        self.assertFalse(Student.objects.filter(UserID=user).exists())
        self.assertFalse(Tutor.objects.filter(UserID=user).exists())

    def test_no_profile_created_for_invalid_role(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create(username="@invalidrole", email="invalidrole@example.com", role="invalid")

        self.assertIn("Invalid role: invalid.", str(context.exception))

    def test_no_duplicate_profiles_on_save(self):
        user = User.objects.create(username="@petrapickles", email="petrapickles@example.com", role="student")
        self.assertTrue(Student.objects.filter(UserID=user).exists())

        user.save()  # Saving again should not create duplicate profiles
        self.assertEqual(Student.objects.filter(UserID=user).count(), 1)

    def test_clean_up_on_delete(self):
        user = User.objects.create(username="@janedoe", email="janedoe@example.com", role="tutor")
        self.assertTrue(Tutor.objects.filter(UserID=user).exists())
        user.delete()
        self.assertFalse(Tutor.objects.filter(UserID=user.id).exists())