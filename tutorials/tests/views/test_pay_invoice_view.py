from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User
from django.utils import timezone
from tutorials.models import Student, Invoice

class PayInvoiceViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_user(username='adminuser', password='adminpass')
        self.admin_user.role = 'admin'
        self.admin_user.save()

        self.student_user = User.objects.create_user(username='studentuser', password='studentpass')
        self.student_user.role = 'student'
        self.student_user.save()

        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.other_user.role = 'tutor'
        self.other_user.save()

        self.student = Student.objects.create(UserID=self.student_user)
        self.invoice = Invoice.objects.create(student=self.student, paid=False, total_amount=100.0)

        self.pay_invoice_url = reverse('pay_invoice', args=[self.invoice.id])
        self.dashboard_url = reverse('dashboard')

    def test_pay_invoice_requires_login(self):
        response = self.client.get(self.pay_invoice_url)
        self.assertNotEqual(response.status_code, 200)

    def test_pay_invoice_student_owns_invoice(self):
        self.client.login(username='studentuser', password='studentpass')
        # GET request
        response = self.client.get(self.pay_invoice_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pay_invoice.html')

        # POST request to pay
        response = self.client.post(self.pay_invoice_url)
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.paid)
        self.assertIsNotNone(self.invoice.date_paid)
        invoice_detail_url = reverse('invoice_detail', args=[self.invoice.id])
        self.assertRedirects(response, invoice_detail_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any(f"Invoice {self.invoice.id} marked as paid." in str(m.message) for m in messages))

    def test_pay_invoice_student_not_own_invoice(self):
        self.client.login(username='otheruser', password='otherpass')
        response = self.client.post(self.pay_invoice_url)
        self.assertRedirects(response, self.dashboard_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("You are not authorized" in str(m.message) for m in messages))
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.paid)

    def test_pay_invoice_admin_cannot_pay(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(self.pay_invoice_url)
        self.assertRedirects(response, self.dashboard_url)
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.paid)
