from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User
from tutorials.models import Student, Lesson, Invoice, Tutor
from datetime import date

class CreateInvoiceViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='@testuser',
            password='testpass',
            first_name='Jahn',
            last_name='Doe',
            role="student"
        )
        self.tutor_user = User.objects.create_user(
            username='@tutoruser',
            password='testpass',
            first_name='Jane',
            last_name='Smith',
            role = "tutor"
        )
        
        # Create Tutor and Student instances
        self.tutor = Tutor.objects.get_or_create(UserID=self.tutor_user)
        self.student = Student.objects.get_or_create(UserID=self.user)

        # URL for create_invoice (adjust if your URL differs)
        self.url = reverse('create_invoice', args=[self.student.id])

    def test_login_required(self):
        """Accessing create_invoice without login should redirect to login page."""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f'/log_in?next={self.url}')

    def test_student_does_not_exist(self):
        """If the student does not exist, the view should return 404."""
        self.client.login(username='testuser', password='testpass')
        invalid_url = reverse('create_invoice', args=[9999])  # ID that doesn't exist
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_no_lessons_to_invoice(self):
        """If there are no lessons to invoice, it should redirect to student_list with an error message."""
        self.client.login(username='testuser', password='testpass')
        # No lessons for this student yet
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('student_list'))
        
        # Check the message
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("No lessons to invoice" in str(m.message) for m in messages))

    def test_get_request_with_lessons(self):
        """On a GET request, if lessons exist, it should render the template with lessons and student."""
        self.client.login(username='testuser', password='testpass')
        # Create lessons that are not invoiced
        lesson1 = Lesson.objects.create(
            student=self.student, 
            tutor=self.tutor, 
            date=date(2024, 1, 10),
            cost=100.0
        )
        lesson2 = Lesson.objects.create(
            student=self.student, 
            tutor=self.tutor, 
            date=date(2024, 1, 11),
            cost=150.0
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_invoice.html')
        self.assertIn('lessons', response.context)
        self.assertIn(lesson1, response.context['lessons'])
        self.assertIn(lesson2, response.context['lessons'])
        self.assertIn('student', response.context)
        self.assertEqual(response.context['student'], self.student)

    def test_post_request_creates_invoice(self):
        """On a POST request, if lessons exist, it should create an invoice and redirect to invoice_details."""
        self.client.login(username='testuser', password='testpass')
        lesson1 = Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            date=date(2024, 1, 10),
            cost=100.0
        )
        lesson2 = Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            date=date(2024, 1, 11),
            cost=150.0
        )

        response = self.client.post(self.url, {})
        # Check that we are redirected to invoice_details after creation
        self.assertEqual(response.status_code, 302)

        # Check the invoice was created
        invoice = Invoice.objects.last()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.student, self.student)
        self.assertEqual(invoice.tutor, self.tutor)
        self.assertFalse(invoice.paid)
        self.assertQuerysetEqual(invoice.lessons.all(), [repr(lesson1), repr(lesson2)], ordered=False)

        # Check if total_amount is calculated correctly
        self.assertAlmostEqual(invoice.total_amount, 250.0)

        # Check redirect URL
        invoice_details_url = reverse('invoice_details', args=[invoice.id])
        self.assertRedirects(response, invoice_details_url)

        # Check success message
        messages = list(response.wsgi_request._messages)
        full_name = f"{self.user.first_name} {self.user.last_name}"
        self.assertTrue(any(f"Invoice {invoice.id} created for {full_name}." in str(m.message) for m in messages))
        