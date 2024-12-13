from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Student, Lesson, Tutor, Language, Invoice
from django.contrib.messages import get_messages

User = get_user_model()

class StudentInvoicesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data for the entire TestCase. This method is run once for the TestCase.
        """

        cls.language = Language.objects.create(name='english')

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


        cls.admin_user = User.objects.create_user(
            username='@adminuser',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )


        cls.student_invoices_url = reverse('student_invoices')
        cls.dashboard_url = reverse('dashboard')

        cls.invoice1 = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=100.00,
            paid=False,
            approved=False
        )
        cls.invoice2 = Invoice.objects.create(
            student=cls.student,
            tutor=cls.tutor,
            total_amount=200.00,
            paid=True,
            approved=True
        )

    def setUp(self):
        """
        Set up a fresh Client instance for each test method.
        """
        self.client = Client()

    def test_student_invoices_requires_login(self):
        """
        Student invoices view should redirect to login if user is not authenticated.
        """
        response = self.client.get(self.student_invoices_url)
        self.assertNotEqual(response.status_code, 200)

        self.assertRedirects(response, f'/log_in/?next={self.student_invoices_url}')

    def test_student_invoices_no_student_profile_redirects(self):
        """
        If the user doesn't have a student profile, they are redirected to the dashboard with an error message.
        """

        self.client.login(username='@adminuser', password='adminpass')
        response = self.client.get(self.student_invoices_url)
        self.assertRedirects(response, self.dashboard_url)


        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You are not authorized to view this page." in message.message for message in messages))

    def test_student_invoices_with_no_invoices(self):
        """
        Test that a student with no invoices sees an empty invoice list.
        """

        new_student_user = User.objects.create_user(
            username='@studentuser2',
            email='student2@example.com',
            password='studentpass2',
            role='student'
        )

        new_student = Student.objects.get(UserID=new_student_user)


        self.client.login(username='@studentuser2', password='studentpass2')
        response = self.client.get(self.student_invoices_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_list.html')
        self.assertIn('invoices', response.context)

        invoices = response.context['invoices']
        self.assertEqual(invoices.count(), 0)


    def test_student_invoices_with_invoices(self):
        """
        Test that a student with invoices sees the correct invoices listed.
        """

        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.student_invoices_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_list.html')
        self.assertIn('invoices', response.context)

        invoices = response.context['invoices']
        self.assertEqual(invoices.count(), 2)
        self.assertIn(self.invoice1, invoices)
        self.assertIn(self.invoice2, invoices)

        content = response.content.decode('utf-8')
        self.assertIn(f'<a href="/invoices/{self.invoice1.id}/">Invoice {self.invoice1.id}</a>', content)
        self.assertIn(f'$100.00', content)
        self.assertIn(f'<a href="/invoices/{self.invoice2.id}/">Invoice {self.invoice2.id}</a>', content)
        self.assertIn(f'$200.00', content)

    def test_student_invoices_template_content(self):
        """
        Ensure that the invoice_list.html template displays the invoices correctly.
        """

        self.client.login(username='@studentuser', password='studentpass')
        response = self.client.get(self.student_invoices_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_list.html')

        content = response.content.decode('utf-8')

        self.assertIn(f'<a href="/invoices/{self.invoice1.id}/">Invoice {self.invoice1.id}</a>', content)
        self.assertIn(f'$100.00', content)

        self.assertIn(f'<a href="/invoices/{self.invoice2.id}/">Invoice {self.invoice2.id}</a>', content)
        self.assertIn(f'$200.00', content)