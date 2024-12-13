from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

import datetime

from tutorials.models import TutorAvailability, Tutor, User

class TutorAvailabilityModelTestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)
        start_time = datetime.time(9, 0)
        end_time = datetime.time(10, 0)
        day = datetime.datetime(2024, 9, 1)
        availability_status = "available"
        self.availability = TutorAvailability(tutor=self.tutor, start_time=start_time, end_time=end_time, day=day, availability_status=availability_status)

    def test_is_valid(self):
        try:
            self.availability.full_clean()
        except ValidationError:
            self.fail("Default form is invalid")

    def test_invalid_time(self):
        self.availability.start_time = datetime.time(11, 0)
        self.availability.end_time = datetime.time(10, 0)
        with self.assertRaises(ValidationError) as context:
            self.availability.clean()
        self.assertEqual(str(context.exception.messages[0]), 'Start time must be before end time.')


    def test_str_method(self):
    # Format the date and time as expected in the string
        expected_date = self.availability.day.strftime("%Y-%m-%d %H:%M:%S")
        expected_start_time = self.availability.start_time.strftime("%H:%M:%S")
        expected_end_time = self.availability.end_time.strftime("%H:%M:%S")

        expected_string = f"{self.tutor.UserID.full_name()} - {expected_date} - from {expected_start_time} to {expected_end_time} - ({self.availability.availability_status})"
        self.assertEqual(str(self.availability), expected_string)
