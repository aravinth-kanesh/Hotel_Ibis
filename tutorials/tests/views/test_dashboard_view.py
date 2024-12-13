from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime
from tutorials.models import Student, Tutor, Lesson, Invoice, TutorAvailability, Language

User = get_user_model()

class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_user(username="admin_user", role="admin", password="adminpass", email="qwer@test.com")
        self.tutor_user = User.objects.create_user(username="tutor_user", role="tutor", password="tutorpass", email="qwerty@test.com")
        self.student_user = User.objects.create_user(username="student_user", role="student", password="studentpass", email="qwertyuiop@test.com")


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
        self.invoice2 = Invoice.objects.create(
                    student=self.student_profile,
                    tutor=self.tutor_profile,
                    paid=True,
                    total_amount = "40",
                    approved=True
                )
        self.lesson = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2025-01-06",
            time="14:00",
            venue="Room 101",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
            invoice = self.invoice
        )
        self.lesson2 = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2025-01-05",
            time="14:00",
            venue="Room 101",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
            invoice = self.invoice2
        )
        self.tutor_availability = TutorAvailability.objects.create(
            tutor=self.tutor_profile,
            day="2024-12-05",
            start_time="14:00:00",
            end_time="20:00:00",
        )

    def test_admin_dashboard_access(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertIn("users", response.context)
        self.assertIn("student_data", response.context)
        self.assertIn("tutor_data", response.context)
        self.assertIn("lessons_data", response.context)
        self.assertIn("invoices_data", response.context)

    def test_tutor_dashboard_access(self):
        self.client.login(username="tutor_user", password="tutorpass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertIn("lessons", response.context)
        self.assertIn("availabilities", response.context)
        self.assertIn("invoice", response.context)

    def test_student_dashboard_access(self):
        self.client.login(username="student_user", password="studentpass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertIn("lessons", response.context)
        self.assertIn("invoice", response.context)

    def test_admin_dashboard_filters(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"), {"action_filter": "allocated"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("student_data" in response.context)

    def test_admin_dashboard_search(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"), {"search": "student_user"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("users" in response.context)
        self.assertTrue(self.student_user.username in [user.username for user in response.context["users"]])

    def test_admin_dashboard_sort(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"), {"sort": "this month"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("lessons_data" in response.context)

    def test_pagination(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"), {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)

    def test_unauthenticated_user_redirect(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("log_in")))

    def test_invalid_role_access(self):
        # Create a user with no role
        user = User.objects.create_user(username="no_role_user", password="norolepass")
        self.client.login(username="no_role_user", password="norolepass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertEqual(response.context["tab"], "accounts")  
        
    def test_sort_by_invoice(self):
        """Test sorting lessons by unique invoices."""
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse('dashboard'), {'sort': 'invoice'})
        self.assertEqual(response.status_code, 200)
        lessons_data = response.context['lessons_data']
        self.assertEqual(len(lessons_data), 2)  
        self.assertIn('lesson', lessons_data[0]) 
    def test_sort_all(self):
        """Test sorting all lessons."""
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse('dashboard'), {'sort': 'all'})
        self.assertEqual(response.status_code, 200)
        lessons_data = response.context['lessons_data']
        self.assertEqual(len(lessons_data), 2)  
        self.assertIn('lesson', lessons_data[0]) 

    def test_sort_this_month(self):
        """Test sorting lessons for the current month."""
        self.client.login(username="admin_user", password="adminpass")
        now = datetime.now()
        Lesson.objects.create(
            student=self.student_profile, tutor=self.tutor_profile, language=self.language,
            date=now.strftime("%Y-%m-%d"), time="12:00:00", invoice=None
        )
        response = self.client.get(reverse('dashboard'), {'sort': 'this month'})
        self.assertEqual(response.status_code, 200)
        lessons_data = response.context['lessons_data']
        self.assertEqual(len(lessons_data), 1)  
        self.assertIn('lesson', lessons_data[0])  
        
    def test_sort_by_invoice_no_invoice(self):
        """Test sorting lessons when no invoice is associated."""
        self.client.login(username="admin_user", password="adminpass")
        Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2024-12-06",
            time="15:00:00",
            venue="Room 102",
            duration=90,
            frequency="once per fortnight",
            term="jan-easter",
            invoice=None,  # No invoice associated
        )
        response = self.client.get(reverse('dashboard'), {'sort': 'invoice'})
        self.assertEqual(response.status_code, 200)
        lessons_data = response.context['lessons_data']
        self.assertTrue(len(lessons_data) >= 1)  # Ensure it doesn't break
        for lesson in lessons_data:
            self.assertIn('lesson', lesson)
    def test_pagination_out_of_range(self):
        self.client.login(username="admin_user", password="adminpass")
        response = self.client.get(reverse("dashboard"), {"page": 999})  # Beyond the range
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)
        self.assertFalse(response.context["page_obj"].has_next())  # No next page
    def test_dashboard_no_lessons(self):
        self.client.login(username="admin_user", password="adminpass")
        Lesson.objects.all().delete()  # Remove all lessons
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("lessons_data", response.context)
        self.assertEqual(len(response.context["lessons_data"]), 0)


    def test_tutor_dashboard_no_availabilities(self):
        self.client.login(username="tutor_user", password="tutorpass")
        TutorAvailability.objects.filter(tutor=self.tutor_profile).delete()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("availabilities", response.context)
        self.assertEqual(len(response.context["availabilities"]), 0)

