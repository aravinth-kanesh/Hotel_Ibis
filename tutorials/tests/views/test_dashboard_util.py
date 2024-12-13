from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Student, Lesson, Invoice, StudentRequest, Language, Tutor, TutorAvailability
from tutorials.views import get_allocated_lesson, get_unallocated_requests 

User = get_user_model()

class AdminViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create an admin user and other users
        self.admin_user = User.objects.create_user(username="admin_user", role="admin", password="adminpass", email="qwer@test.com")
        self.student_user = User.objects.create_user(username="student_user", role="student", password="studentpass" , email="qwtyjker@test.com")
        self.tutor_user = User.objects.create_user(username="tutor_user", role="tutor", password="tutorpass", email="qwertyur@test.com")

\
        self.student_profile, _  = Student.objects.get_or_create(UserID=self.student_user)
        self.tutor_profile, _  = Tutor.objects.get_or_create(UserID=self.tutor_user)
        self.language = Language.objects.create(name="Python")
        self.tutor_profile.languages.add(self.language)
        self.invoice = Invoice.objects.create(
                    student=self.student_profile,
                    tutor=self.tutor_profile,
                    paid=False,
                    total_amount = "20",
                )
        
        self.lesson = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2024-12-05",
            time="14:00",
            venue="Room 101",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
            invoice = self.invoice
        )
        
        self.tutor_availability = TutorAvailability.objects.create(
            tutor=self.tutor_profile,
            day="2024-12-05",
            start_time="14:00:00",
            end_time="20:00:00",
        )

        self.student_request = StudentRequest.objects.create(
            student=self.student_profile,
            language=self.language,
            description="Request for Python lessons.",
            date="2024-12-15",
            time="14:00:00",
            venue="Classroom 2",
            duration=90,
            frequency="once per fortnight",
            term="jan-easter"
        )

    def test_update_user_role_as_admin(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.post(reverse("update_user_role", args=[self.student_user.id]), {"role": "tutor"})
        self.assertEqual(response.status_code, 302)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.role, "tutor")

    def test_update_user_role_as_non_admin(self):
        self.client.login(username="student_user", password="studentpass")
        response = self.client.post(reverse("update_user_role", args=[self.tutor_user.id]), {"role": "student"})
        self.assertEqual(response.status_code, 403) 

    def test_delete_user_as_admin(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.post(reverse("delete_user", args=[self.student_user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.student_user.id).exists())

    def test_delete_user_as_non_admin(self):
        self.client.login(username="student_user", password="studentpass")
        response = self.client.post(reverse("delete_user", args=[self.tutor_user.id]))
        self.assertEqual(response.status_code, 403)  

    def test_get_unallocated_requests(self):
        unallocated_request = get_unallocated_requests(self.student_profile)
        self.assertIsNotNone(unallocated_request)
        self.assertEqual(unallocated_request, self.student_request)

    def test_get_allocated_lesson(self):
        allocated_lesson = get_allocated_lesson(self.student_profile)
        self.assertIsNotNone(allocated_lesson)
        self.assertEqual(allocated_lesson, self.lesson)

    def test_approve_invoice_as_admin(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.post(reverse("approve_invoice", args=[self.invoice.id]))
        self.assertEqual(response.status_code, 302)
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.approved)

    def test_approve_invoice_as_non_admin(self):
        self.client.login(username="student_user", password="studentpass")
        response = self.client.post(reverse("approve_invoice", args=[self.invoice.id]))
        self.assertEqual(response.status_code, 403) 
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.approved)

    def test_redirect_for_unauthenticated_users(self):
        response = self.client.post(reverse("update_user_role", args=[self.student_user.id]), {"role": "tutor"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("log_in")))

        response = self.client.post(reverse("delete_user", args=[self.student_user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

        response = self.client.post(reverse("approve_invoice", args=[self.invoice.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

