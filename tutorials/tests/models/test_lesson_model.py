from django.test import TestCase
from datetime import date, time
from tutorials.models import Lesson, Tutor, Student, Language, Invoice, User
from decimal import Decimal

class LessonModelTest(TestCase):
    def setUp(self):
        """Set up test data for all tests."""
        self.tutor_user = User.objects.create(
            username="tutor123", first_name="Jane", last_name="Smith", email="tutor@example.com"
        )
        self.student_user = User.objects.create(
            username="student123", first_name="John", last_name="Doe", email="student@example.com"
        )

        self.tutor, _ = Tutor.objects.get_or_create(UserID=self.tutor_user)
        self.student, _ = Student.objects.get_or_create(UserID=self.student_user)
        self.language, _ = Language.objects.get_or_create(name="French")

        self.invoice = Invoice.objects.create(
            student=self.student,
            tutor=self.tutor,
            total_amount=0,
            paid=False,
            approved=False
        )

        self.lesson = Lesson.objects.create(
            tutor=self.tutor,
            student=self.student,
            language=self.language,
            invoice=self.invoice,
            time=time(10, 0),
            date=date(2024, 1, 10),
            venue="Classroom A",
            duration=90,
            frequency='once a week',
            term='jan-easter',
            price=Decimal('100.00')
        )

    def test_lesson_creation(self):
        """Test that a lesson is created correctly."""
        self.assertIsInstance(self.lesson, Lesson)
        self.assertEqual(self.lesson.tutor, self.tutor)
        self.assertEqual(self.lesson.student, self.student)
        self.assertEqual(self.lesson.language, self.language)
        self.assertEqual(self.lesson.venue, "Classroom A")
        self.assertEqual(self.lesson.duration, 90)
        self.assertEqual(self.lesson.frequency, 'once a week')
        self.assertEqual(self.lesson.term, 'jan-easter')
        self.assertEqual(self.lesson.price, Decimal('100.00'))

    def test_lesson_str(self):
        """Test the string representation of a lesson."""
        expected_str = f"Lesson {self.lesson.id} (french) with {self.student.UserID.username} on 2024-01-10 at 10:00:00"
        self.assertEqual(str(self.lesson), expected_str)

    def test_get_price(self):
        """Test the get_price method."""
        self.assertEqual(self.lesson.get_price(), Decimal('100.00'))

    def test_lesson_duration(self):
        """Test that the lesson duration is correctly set."""
        self.assertEqual(self.lesson.duration, 90)

    def test_lesson_price_update(self):
        """Test that the lesson price can be updated."""
        self.lesson.price = Decimal('150.00')
        self.lesson.save()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.price, Decimal('150.00'))

    def test_lesson_without_invoice(self):
        """Test that a lesson can exist without an associated invoice."""
        self.lesson.invoice = None
        self.lesson.save()
        self.assertIsNone(self.lesson.invoice)

    def test_lesson_time(self):
        """Test that the lesson time is correctly set."""
        self.assertEqual(self.lesson.time, time(10, 0))

    def test_lesson_date(self):
        """Test that the lesson date is correctly set."""
        self.assertEqual(self.lesson.date, date(2024, 1, 10))

    def test_lesson_term_mismatch(self):
        """Test get_occurrence_dates with a mismatched term."""
        self.lesson.term = 'sept-christmas'  # Mismatched term
        self.assertEqual(self.lesson.get_occurrence_dates(), [])