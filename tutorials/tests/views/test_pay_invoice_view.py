from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Student, Tutor, Language, Invoice
from django.utils import timezone
from django.contrib.messages import get_messages

User = get_user_model()

class PayInvoiceViewTestCase(TestCase):
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

        # Create a student user (signals auto-create Student profile)
        cls.student_user = User.objects.create_user(
            username='@studentuser',
            email='student@example.com',
            password='studentpass',
            role='student'
        )
        cls.student = Student.objects.get(UserID=cls.student_user)

        cls.other_student_user = User.objects.create_user(
            username='@otherstudent',
            email='otherstudent@example.com',
            password='otherpass',
            role='student'
        )
        cls.other_student = Student.objects.get(UserID=cls.other_student_user)

        cls.admin_user = User.objects.create_user(
            username='@adminuser',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )

        cls.pay_invoice_url = lambda invoice_id: reverse('pay_invoice', args=[invoice_id])
        cls.invoice_detail_url = lambda invoice_id: reverse('invoice_detail', args=[invoice_id])
        cls.dashboard_url = reverse('dashboard')

        cls.invoice = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=150.00,
            paid=False,
            approved=True
        )

    def setUp(self):
        """
        Set up a fresh Client instance for each test method.
        """
        self.client = Client()

    def test_redirect_if_not_logged_in(self):
        """
        Ensure that unauthenticated users are redirected to the login page.
        """
        response = self.client.get(self.pay_invoice_url(self.invoice.id))
        self.assertNotEqual(response.status_code, 200)

        expected_redirect = f'/log_in/?next={self.pay_invoice_url(self.invoice.id)}'
        self.assertRedirects(response, expected_redirect)

    def test_pay_invoice_get_as_owner(self):
        """
        Ensure that the student can access the pay_invoice page for their own invoice via GET.
        """
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.pay_invoice_url(self.invoice.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pay_invoice.html')
        self.assertIn('invoice', response.context)
        self.assertEqual(response.context['invoice'], self.invoice)

    def test_pay_invoice_post_as_owner(self):
        """
        Ensure that the student can mark their own invoice as paid via POST.
        """
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.post(self.pay_invoice_url(self.invoice.id))

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.paid)
        self.assertIsNotNone(self.invoice.date_paid)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(f"Invoice {self.invoice.id} marked as paid." in message.message for message in messages))

        self.assertRedirects(response, self.invoice_detail_url(self.invoice.id))

    def test_pay_invoice_get_as_non_owner(self):
        """
        Ensure that a student cannot access the pay_invoice page for someone else's invoice.
        """
        self.client.login(username='@otherstudent', password='otherpass')
        response = self.client.get(self.pay_invoice_url(self.invoice.id))
        self.assertRedirects(response, self.dashboard_url)
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You are not authorized to perform this action." in message.message for message in messages))

    def test_pay_invoice_post_as_non_owner(self):
        """
        Ensure that a student cannot mark someone else's invoice as paid via POST.
        """
        self.client.login(username='@otherstudent', password='otherpass')
        response = self.client.post(self.pay_invoice_url(self.invoice.id))

        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.paid)
        self.assertIsNone(self.invoice.date_paid)
        self.assertRedirects(response, self.dashboard_url)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You are not authorized to perform this action." in message.message for message in messages))

    def test_pay_invoice_invalid_invoice_id(self):
        """
        Ensure that accessing a non-existent invoice results in a 404 error.
        """
        invalid_invoice_id = 9999 
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.pay_invoice_url(invalid_invoice_id))
        self.assertEqual(response.status_code, 404)

    def test_pay_invoice_as_admin(self):
        """
        Ensure that an admin cannot pay a student's invoice and is redirected to the dashboard.
        """
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.post(self.pay_invoice_url(self.invoice.id))

        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.paid)
        self.assertIsNone(self.invoice.date_paid)
        self.assertRedirects(response, self.dashboard_url)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You are not authorized to perform this action." in message.message for message in messages))
