from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User
from tutorials.models import Student, Invoice

class StudentInvoicesAdminViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_user(username='adminuser', password='adminpass', first_name="A", last_name="B")
        self.admin_user.role = 'admin'
        self.admin_user.save()

        self.student_user = User.objects.create_user(username='studentuser', password='studentpass',  first_name="C", last_name="D")
        self.student_user.role = 'student'
        self.student_user.save()

        self.student = Student.objects.create(UserID=self.student_user)
        self.invoice = Invoice.objects.create(student=self.student, paid=False, total_amount=100.0)
        self.student_invoices_admin_url = reverse('student_invoices_admin', args=[self.student.id])
        self.dashboard_url = reverse('dashboard')

    def test_student_invoices_admin_requires_login(self):
        response = self.client.get(self.student_invoices_admin_url)
        self.assertNotEqual(response.status_code, 200)

    def test_student_invoices_admin_view_as_admin(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(self.student_invoices_admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_invoices_admin.html')
        self.assertIn(self.invoice, response.context['invoices'])

    def test_student_invoices_admin_view_as_non_admin(self):
        self.client.login(username='studentuser', password='studentpass')
        response = self.client.get(self.student_invoices_admin_url)
        self.assertRedirects(response, self.dashboard_url)
