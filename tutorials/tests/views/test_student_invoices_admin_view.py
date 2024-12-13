from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Student, Tutor, Language, Invoice

User = get_user_model()

class StudentInvoicesAdminViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data for the entire TestCase. This method is run once for the TestCase.
        """
        cls.language = Language.objects.create(name='English')

        cls.tutor_user = User.objects.create_user(
            username='@tutoruser',
            email='tutor@example.com',
            password='tutorpass',
            role='tutor'
        )
        cls.tutor = Tutor.objects.get(UserID=cls.tutor_user)

        cls.student_user = User.objects.create_user(
            username='@studentuser',
            email='student@example.com',
            password='studentpass',
            role='student'
        )
        cls.student = Student.objects.get(UserID=cls.student_user)

        cls.student_no_invoices_user = User.objects.create_user(
            username='@studentuser2',
            email='student2@example.com',
            password='studentpass2',
            role='student'
        )
        cls.student_no_invoices = Student.objects.get(UserID=cls.student_no_invoices_user)

        cls.admin_user = User.objects.create_user(
            username='@adminuser',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )

        cls.student_invoices_admin_url = lambda student_id: reverse('student_invoices_admin', args=[student_id])
        cls.dashboard_url = reverse('dashboard')

        cls.invoice1 = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=150.00,
            paid=False,
            approved=False
        )
        cls.invoice2 = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=250.00,
            paid=True,
            approved=True
        )

    def setUp(self):
        """
        Set up a fresh Client instance for each test method.
        """
        self.client = Client()

    def test_redirect_if_not_admin(self):
        """
        Ensure that authenticated non-admin users are redirected to the dashboard.
        """
        student_id = self.student.id
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.student_invoices_admin_url(student_id))
        self.assertRedirects(response, self.dashboard_url)

    def test_admin_access_with_valid_student_id_and_invoices(self):
        """
        Ensure that an admin can view a student's invoices when invoices exist.
        """
        student_id = self.student.id
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.student_invoices_admin_url(student_id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_invoices_admin.html')
        self.assertIn('student', response.context)
        self.assertIn('invoices', response.context)

        self.assertEqual(response.context['student'], self.student)

        invoices = response.context['invoices']
        self.assertEqual(invoices.count(), 2)
        self.assertIn(self.invoice1, invoices)
        self.assertIn(self.invoice2, invoices)

    def test_admin_access_with_valid_student_id_no_invoices(self):
        """
        Ensure that an admin can view a student's profile even if there are no invoices.
        """
        student_id = self.student_no_invoices.id
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.student_invoices_admin_url(student_id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_invoices_admin.html')
        self.assertIn('student', response.context)
        self.assertIn('invoices', response.context)

        self.assertEqual(response.context['student'], self.student_no_invoices)

        invoices = response.context['invoices']
        self.assertEqual(invoices.count(), 0)

    def test_admin_access_with_invalid_student_id(self):
        """
        Ensure that accessing a non-existent student results in a 404 error.
        """
        invalid_student_id = 9999
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.student_invoices_admin_url(invalid_student_id))
        self.assertEqual(response.status_code, 404)
