from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal, InvalidOperation


from django.contrib.auth import get_user_model
from tutorials.models import Student, Tutor, Lesson, Invoice, Language

User = get_user_model()

class SetPriceAndCreateInvoiceTests(TestCase):

    def setUp(self):
        self.client = Client()

     
        self.admin_user = User.objects.create_user(username="admin_user", role="admin", password="adminpass", email="qwesdfiop@test.com")
        self.tutor_user = User.objects.create_user(username="tutor_user", role="tutor", password="tutorpass", email="qsdftyuiop@test.com")
        self.student_user = User.objects.create_user(username="student_user", role="student", password="studentpass", email="fgdf@test.com")

    
        self.student_profile, _ = Student.objects.get_or_create(UserID=self.student_user)
        self.tutor_profile, _ = Tutor.objects.get_or_create(UserID=self.tutor_user)

     
        self.language = Language.objects.create(name="Python")

     
        self.lesson1 = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2024-12-10",
            time="14:00:00",
            venue="Room 101",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
        )
        self.lesson2 = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor_profile,
            language=self.language,
            date="2024-12-17",
            time="14:00:00",
            venue="Room 102",
            duration=60,
            frequency="once a week",
            term="sept-christmas",
        )

    def test_set_price_as_admin(self):
        self.client.login(username="admin_user", password="adminpass")
        url = reverse('set_price', args=[self.student_profile.id])
        response = self.client.post(url, {'price': '50.00'})

        self.assertEqual(response.status_code, 302)  
        self.lesson1.refresh_from_db()
        self.lesson2.refresh_from_db()
        self.assertEqual(self.lesson1.price, Decimal('50.00'))
        self.assertEqual(self.lesson2.price, Decimal('50.00'))

    def test_set_price_as_non_admin(self):
        self.client.login(username="tutor_user", password="tutorpass")
        url = reverse('set_price', args=[self.student_profile.id])
        response = self.client.post(url, {'price': '50.00'})

        self.assertEqual(response.status_code, 302)  
        self.lesson1.refresh_from_db()
        self.lesson2.refresh_from_db()
        self.assertEqual(self.lesson1.price, Decimal('0.00'))

        self.assertEqual(self.lesson2.price, Decimal('0.00'))


    def test_create_invoice_as_admin(self):
        self.lesson1.price = Decimal('50.00')
        self.lesson1.save()
        self.lesson2.price = Decimal('50.00')
        self.lesson2.save()

        self.client.login(username="admin_user", password="adminpass")
        url = reverse('create_invoice', args=[self.student_profile.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302) 
        invoice = Invoice.objects.get(student=self.student_profile)
        self.assertEqual(invoice.total_amount, Decimal('100.00'))  
        self.assertTrue(Lesson.objects.filter(invoice=invoice).exists())

    def test_create_invoice_with_no_lessons(self):
        self.lesson1.invoice = Invoice.objects.create(student=self.student_profile, tutor=self.tutor_profile, total_amount=0.0)
        self.lesson1.save()
        self.lesson2.invoice = self.lesson1.invoice
        self.lesson2.save()

        self.client.login(username="admin_user", password="adminpass")
        url = reverse('create_invoice', args=[self.student_profile.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302) 
        self.assertFalse(Invoice.objects.filter(student=self.student_profile, total_amount__gt=0).exists())

    def test_create_invoice_as_non_admin(self):
        self.client.login(username="tutor_user", password="tutorpass")
        url = reverse('create_invoice', args=[self.student_profile.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)  
        self.assertFalse(Invoice.objects.filter(student=self.student_profile).exists())