from django.test import TestCase
from tutorials.models import Invoice, Student, Tutor, Lesson, Language, User
from decimal import Decimal

class InvoiceTest(TestCase):

    def setUp(self):
        """Set up test data for all tests."""
        self.student_user = User.objects.create(
            username="student123", first_name="John", last_name="Doe", email="student@example.com"
        )
        self.tutor_user = User.objects.create(
            username="tutor123", first_name="Jane", last_name="Smith", email="tutor@example.com"
        )

        self.student, _ = Student.objects.get_or_create(UserID=self.student_user)
        self.tutor, _ = Tutor.objects.get_or_create(UserID=self.tutor_user)

        self.language, _ = Language.objects.get_or_create(name="English")

        self.tutor.languages.add(self.language)

        self.lesson = Lesson.objects.create(
            tutor=self.tutor,
            student=self.student,
            language=self.language,
            price=50.00,
            time="09:00",  
            date="2024-12-11",  
            venue="Classroom 1",
            duration=60,  
            frequency='once a week',
            term='sept-christmas'
        )

    def test_invoice_creation(self):
        """Test that an invoice can be created and saved correctly."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0,  
            paid=False,
            approved=False
        )
        self.assertIsInstance(invoice, Invoice)
        self.assertEqual(invoice.student, self.student)
        self.assertEqual(invoice.tutor, self.tutor)
        self.assertEqual(invoice.total_amount, 0)  
        self.assertFalse(invoice.paid)
        self.assertFalse(invoice.approved)

    def test_invoice_str(self):
        """Test the string representation of the invoice."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=100.00,
            paid=False,
            approved=False
        )
        self.assertEqual(str(invoice), "Invoice 1 (Unpaid)")  

    def test_calculate_total_amount(self):
        """Test the calculate_total_amount method."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0,  
            paid=False,
            approved=False
        )
        
        # Create multiple lessons
        Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=50.00, language=self.language)
        Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=50.00, language=self.language)

        # Calculate the total amount
        invoice.calculate_total_amount()

        expected_total = 2 * 50.00  # 2 lessons, each priced at 50.00
        self.assertEqual(invoice.total_amount, expected_total)

    def test_calculate_total_amount_with_no_lessons(self):
        """Test calculate_total_amount when no lessons are associated."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0, 
            paid=False,
            approved=False
        )

        # Ensure that total_amount remains 0 when no lessons are present
        invoice.calculate_total_amount()
        self.assertEqual(invoice.total_amount, 0)

    def test_invoice_paid_status(self):
        """Test updating the paid status of an invoice."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=100.00,
            paid=False,
            approved=False
        )
        
        # Mark the invoice as paid
        invoice.paid = True
        invoice.save()

        # Reload the invoice from the database and check the paid status
        invoice.refresh_from_db()
        self.assertTrue(invoice.paid)

    def test_invoice_approved_status(self):
        """Test updating the approved status of an invoice."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=100.00,
            paid=False,
            approved=False
        )
        
        # Mark the invoice as approved
        invoice.approved = True
        invoice.save()

        # Reload the invoice from the database and check the approved status
        invoice.refresh_from_db()
        self.assertTrue(invoice.approved)

    def test_calculate_total_amount_after_adding_lessons(self):
        """Test that total_amount is recalculated when new lessons are added."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0,
            paid=False,
            approved=False
        )
        
        # Add a lesson
        lesson1 = Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=50.00, language=self.language)
        invoice.calculate_total_amount()
        self.assertEqual(invoice.total_amount, lesson1.price)

        # Add another lesson
        lesson2 = Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=60.00, language=self.language)
        invoice.calculate_total_amount()
        self.assertEqual(invoice.total_amount, lesson1.price + lesson2.price)

    def test_calculate_total_amount_with_decimal(self):
        """Test that total_amount handles decimal values correctly."""
        invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0,
            paid=False,
            approved=False
        )
        
        # Add a lesson with a price that includes decimals
        lesson1 = Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=49.99, language=self.language)
        lesson2 = Lesson.objects.create(invoice=invoice, tutor=self.tutor, student=self.student, price=50.01, language=self.language)
        
        invoice.calculate_total_amount()
        expected_total = Decimal('49.99') + Decimal('50.01')
        self.assertEqual(invoice.total_amount, expected_total)