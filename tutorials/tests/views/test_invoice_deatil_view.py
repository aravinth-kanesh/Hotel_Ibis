from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tutorials.models import Student, Invoice

class InvoiceDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Users
        self.admin_user = User.objects.create_user(username='adminuser', password='adminpass')
        self.admin_user.role = 'admin'
        self.admin_user.save()

        self.student_user = User.objects.create_user(username='studentuser', password='studentpass')
        self.student_user.role = 'student'
        self.student_user.save()

        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.other_user.role = 'tutor'
        self.other_user.save()

        # Student/Invoice
        self.student = Student.objects.create(UserID=self.student_user)
        self.invoice = Invoice.objects.create(student=self.student, paid=False, total_amount=100.0)

        self.invoice_detail_url = reverse('invoice_detail', args=[self.invoice.id])
        self.dashboard_url = reverse('dashboard')

    def test_invoice_detail_requires_login(self):
        response = self.client.get(self.invoice_detail_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn('/log_in?next=', response.url)

    def test_invoice_detail_admin_can_view_any_invoice(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(self.invoice_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_details.html')
        self.assertEqual(response.context['invoice'], self.invoice)

    def test_invoice_detail_student_can_only_view_own_invoice(self):
        self.client.login(username='studentuser', password='studentpass')
        response = self.client.get(self.invoice_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_details.html')

        # Another user attempts to view
        self.client.login(username='otheruser', password='otherpass')
        response = self.client.get(self.invoice_detail_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_invoice_detail_other_roles_redirected(self):
        self.client.login(username='otheruser', password='otherpass')
        response = self.client.get(self.invoice_detail_url)
        self.assertRedirects(response, self.dashboard_url)