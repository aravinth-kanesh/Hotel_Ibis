from datetime import date, datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import StudentRequest, Tutor, Student, Language, Lesson
from django.utils import timezone

#Test commit

class StudentRequestProcessingViewTestCase(TestCase):
    """Test suite for the StudentRequestProcessingView where the admin user processes student requests."""
    """Commit test"""

    def setUp(self):
        # Create an admin 
        self.user_admin = get_user_model().objects.create_user(
            username='@admin_user',
            first_name='Admin',
            last_name='User',
            email='admin.user@example.com',
            password='adminpassword',
            role='admin'  
        )

        # Create a tutor 
        self.user_tutor = get_user_model().objects.create_user(
            username='@john_doe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            password='password123',
            role='tutor'
        )

        # Create a student 
        self.user_student = get_user_model().objects.create_user(
            username='@jane_smith',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            password='password123',
            role='student'
        )

        # Create a language
        self.language = Language.objects.create(name="Python")

        # Create tutor and student instances
        self.tutor = Tutor.objects.create(UserID=self.user_tutor)
        self.student = Student.objects.create(UserID=self.user_student)

        # Create a student request
        self.student_request = StudentRequest.objects.create(
            student=self.student,
            language=self.language,
            description="Looking for a tutor for Python",
            is_allocated=False,
            time="10:00",
            venue="BH 6.02",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )

    def test_admin_can_access_student_request_processing_form(self):
        """Test that the admin can access the student request processing form."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Get the URL for processing the student request
        response = self.client.get(reverse('process_request', args=[self.student_request.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'process_request.html')

    def test_reject_student_request(self):
        """Test that rejecting a student request does not create a lesson."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Reject the request by posting with status 'denied'
        self.client.post(reverse('process_request', args=[self.student_request.id]), {
            'status': 'denied',
            'details': 'The student is unavailable at the requested time.',
        })

        # Check that no lesson was created
        lesson = Lesson.objects.filter(student=self.student, tutor=self.tutor).first()
        self.assertIsNone(lesson)

        # Ensure the request is now marked as 'denied'
        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.is_allocated, False)

    def test_all_lessons_scheduled_for_term(self):
        """Test that all lessons for the specified term are booked according to the frequency."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Accept the request by posting with status 'accepted' and specifying the first lesson date and time
        self.client.post(reverse('process_request', args=[self.student_request.id]), {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor.id,
            'first_lesson_date': "2024-09-04",  
            'first_lesson_time': "15:00",  
        })

        lessons = Lesson.objects.filter(student=self.student, tutor=self.tutor)

        term_start = date(2024, 9, 1)
        term_end = date(2024, 12, 25)
        days_between_lessons = 7 if self.student_request.frequency == "once a week" else 14

        # Start date from the request
        current_date = datetime.strptime("2024-09-04", "%Y-%m-%d").date()
        expected_dates = []

        # Generate expected lesson dates
        while current_date <= term_end:
            if current_date >= term_start:
                expected_dates.append(current_date)
            current_date += timedelta(days=days_between_lessons)

        # Verify that the correct number of lessons have been scheduled
        self.assertEqual(lessons.count(), len(expected_dates))

        # Verify that each expected date has a corresponding lesson
        for expected_date in expected_dates:
            self.assertTrue(
                lessons.filter(date=expected_date).exists(),
                f"Lesson on {expected_date} was not scheduled."
            )

        # Verify that all lessons are within the term range
        for lesson in lessons:
            self.assertGreaterEqual(lesson.date, term_start)
            self.assertLessEqual(lesson.date, term_end)

        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.is_allocated, True)

    def test_lesson_rescheduling_due_to_conflict(self):
        """Test that a lesson is rescheduled if there is a conflict for the requested time."""

        self.client.login(username='@admin_user', password='adminpassword')

        # Create a conflict by manually scheduling another lesson for the tutor or student at 3 PM on the same day
        Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            language=self.language,
            time=datetime.strptime("15:00", "%H:%M").time(),
            date=date(2024, 9, 4),
            venue='Existing Venue',
            duration=60,
            frequency='once a week',
            term='sept-christmas'
        )

        # Accept the request and schedule the first lesson at 3 PM on September 4, 2024
        self.client.post(reverse('process_request', args=[self.student_request.id]), {
            'status': 'accepted',
            'details': '',
            'tutor': self.tutor.id,
            'first_lesson_date': "2024-09-04",  
            'first_lesson_time': "15:00",  
        })

        lessons = Lesson.objects.filter(student=self.student, tutor=self.tutor)

        term_start = date(2024, 9, 1)
        term_end = date(2024, 12, 25)
        days_between_lessons = 7 if self.student_request.frequency == "once a week" else 14

        current_date = datetime.strptime("2024-09-04", "%Y-%m-%d").date()
        expected_dates = []

        while current_date <= term_end:
            if current_date >= term_start:
                expected_dates.append(current_date)
            current_date += timedelta(days=days_between_lessons)

        # Ensure there are the correct number of lessons
        self.assertEqual(lessons.count(), len(expected_dates) + 1)

        # Ensure that the conflicting lesson has been rescheduled
        conflicting_lesson = Lesson.objects.get(
            student=self.student,
            tutor=self.tutor,
            date=date(2024, 9, 4),
            time=datetime.strptime("16:00", "%H:%M").time()
        )

        # Check if the lesson was rescheduled
        self.assertNotEqual(conflicting_lesson.time, datetime.strptime("15:00", "%H:%M").time())

        # Ensure that the rescheduled lesson is within the correct time range and does not conflict
        self.assertTrue(conflicting_lesson.time > datetime.strptime("15:00", "%H:%M").time())
        self.assertEqual(conflicting_lesson.date, date(2024, 9, 4))  # Same day but a different time

        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.is_allocated, True)