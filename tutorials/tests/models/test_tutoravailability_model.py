from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import time, date
from tutorials.models import Tutor, TutorAvailability, User


class TutorAvailabilityTestCase(TestCase):
    """Unit tests for the TutorAvailability model."""

    def setUp(self):
        # Create a sample User and Tutor for testing
        self.user = User.objects.create(
            username='@johndoe', 
            first_name='John', 
            last_name='Doe', 
            email='johndoe@example.com', 
        )
        self.tutor, _ = Tutor.objects.get_or_create(UserID=self.user)

    def test_tutor_availability_creation_valid(self):
        """Test creating a TutorAvailability object with valid data."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        self.assertEqual(str(availability), 'John Doe - 2024-01-01 - from 09:00:00 to 17:00:00 - (available)')
        self.assertEqual(availability.tutor, self.tutor)
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))
        self.assertEqual(availability.day, date(2024, 1, 1))
        self.assertEqual(availability.availability_status, 'available')
        self.assertEqual(availability.action, 'edit')

    def test_tutor_availability_invalid_start_time_after_end_time(self):
        """Test that a ValidationError is raised if start_time is after end_time."""
        availability = TutorAvailability(
            tutor=self.tutor,
            start_time=time(17, 0),
            end_time=time(9, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        with self.assertRaises(ValidationError):
            availability.clean()  # This will raise ValidationError because start_time > end_time

    def test_tutor_availability_default_values(self):
        """Test creating a TutorAvailability with default values for start_time and availability_status."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(10, 0),
            day=date(2024, 1, 1)
        )
        self.assertEqual(availability.availability_status, 'available')
        self.assertEqual(availability.action, 'edit')

    def test_tutor_availability_invalid_availability_status(self):
        """Test that creating a TutorAvailability with invalid availability_status raises an error."""
        availability = TutorAvailability(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='busy',  # Invalid value for availability_status
            action='edit'
        )
        with self.assertRaises(ValidationError):
            availability.clean()  # Availability status should be 'available' or 'not_available'

    def test_tutor_availability_invalid_action(self):
        """Test that creating a TutorAvailability with an invalid action raises an error."""
        availability = TutorAvailability(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='remove'  # Invalid value for action
        )
        with self.assertRaises(ValidationError):
            availability.clean()  # Action should be 'edit' or 'delete'

    def test_tutor_availability_string_representation(self):
        """Test that the string representation of TutorAvailability is correct."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        expected_str = 'John Doe - 2024-01-01 - from 09:00:00 to 17:00:00 - (available)'
        self.assertEqual(str(availability), expected_str)

    def test_tutor_availability_not_available_status(self):
        """Test TutorAvailability with 'not_available' status."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='not_available',
            action='edit'
        )
        self.assertEqual(availability.availability_status, 'not_available')
        self.assertEqual(str(availability), 'John Doe - 2024-01-01 - from 09:00:00 to 17:00:00 - (not_available)')

    def test_tutor_availability_edit_action(self):
        """Test TutorAvailability with 'edit' action."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        self.assertEqual(availability.action, 'edit')

    def test_tutor_availability_delete_action(self):
        """Test TutorAvailability with 'delete' action."""
        availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='delete'
        )
        self.assertEqual(availability.action, 'delete')

    def test_tutor_availability_save(self):
        """Test saving a TutorAvailability object."""
        availability = TutorAvailability(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        try:
            availability.save()  # Ensure no exceptions during save
        except Exception as e:
            self.fail(f"Save raised an exception: {e}")

    def test_clean_method_called(self):
        """Test that the clean method is properly called and executes the super().clean()"""
        
        # Creating a valid TutorAvailability instance to trigger the clean() method
        availability = TutorAvailability(
            tutor=self.tutor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            day=date(2024, 1, 1),
            availability_status='available',
            action='edit'
        )
        
        # Calling the clean method, which will invoke super().clean()
        try:
            availability.clean()  # No exception should be raised
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly")