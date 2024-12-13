from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Student, Tutor, Language, Invoice, Lesson
from django.utils import timezone
from django.contrib.messages import get_messages

User = get_user_model()

class InvoiceDetailViewTestCase(TestCase):
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

        cls.invoice_detail_url = lambda invoice_id: reverse('invoice_detail', args=[invoice_id])
        cls.dashboard_url = reverse('dashboard')

        cls.invoice1 = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=150.00,
            paid=False,
            approved=True
        )
        cls.invoice2 = Invoice.objects.create(
            student=cls.other_student,
            tutor=cls.tutor,
            total_amount=250.00,
            paid=True,
            approved=True
        )

        # Create lessons for invoice1
        cls.lesson1 = Lesson.objects.create(
            invoice=cls.invoice1,
            tutor=cls.tutor,
            student=cls.student,
            language=cls.language,
            time=timezone.now().time(),
            date=timezone.now().date(),
            venue='Online',
            duration=60, 
            frequency='once a week',
            term='sept-christmas',
            price=60.00
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
        response = self.client.get(self.invoice_detail_url(self.invoice1.id))
        self.assertNotEqual(response.status_code, 200)
        expected_redirect = f'/log_in/?next={self.invoice_detail_url(self.invoice1.id)}'
        self.assertRedirects(response, expected_redirect)

    def test_student_access_own_invoice(self):
        """
        Ensure that a student can access their own invoice.
        """
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.invoice_detail_url(self.invoice1.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_details.html')
        self.assertIn('invoice', response.context)
        self.assertIn('lessons', response.context)
        self.assertEqual(response.context['invoice'], self.invoice1)
        self.assertEqual(list(response.context['lessons']), [self.lesson1])

    def test_student_access_other_invoice(self):
        """
        Ensure that a student cannot access another student's invoice.
        """
        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.invoice_detail_url(self.invoice2.id))
        self.assertRedirects(response, self.dashboard_url)

        messages = list(get_messages(response.wsgi_request))
        if messages:
            self.assertEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), "You are not authorized to perform this action.")

    def test_admin_access_any_invoice(self):
        """
        Ensure that an admin can access any invoice.
        """
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.invoice_detail_url(self.invoice2.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_details.html')
        self.assertIn('invoice', response.context)
        self.assertIn('lessons', response.context)
        self.assertEqual(response.context['invoice'], self.invoice2)

        self.assertEqual(list(response.context['lessons']), [])

    def test_other_role_access(self):
        """
        Ensure that users with roles other than 'student' or 'admin' are redirected to the dashboard.
        """
        self.client.login(username='@tutoruser', password='tutorpass')
        response = self.client.get(self.invoice_detail_url(self.invoice1.id))
        self.assertRedirects(response, self.dashboard_url)
        messages = list(get_messages(response.wsgi_request))
        if messages:
            self.assertEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), "You are not authorized to perform this action.")

    def test_access_invalid_invoice_id(self):
        """
        Ensure that accessing a non-existent invoice results in a 404 error.
        """
        invalid_invoice_id = 9999 
        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.invoice_detail_url(invalid_invoice_id))
        self.assertEqual(response.status_code, 404)
