from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models import Student, Tutor, TutorAvailability, Lesson, Invoice, Language

class DashboardViewTestCase(TestCase):
    def setUp(self):
        """Set up test data for different user roles and models"""
        
        User = get_user_model()
        self.user_admin = User.objects.create_user(
            username='@admin_user',
            first_name='Admin',
            last_name='User',
            email='admin.user@example.com',
            password='adminpassword',
            role='admin',
        )
        self.user_tutor = User.objects.create_user(
            username='@john_doe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            password='password123',
            role='tutor'
        )
        self.user_student = User.objects.create_user(
            username='@jane_smith',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            password='password123',
            role='student'
        )

        self.student, _ = Student.objects.get_or_create(UserID=self.user_student)
        self.tutor, _ = Tutor.objects.get_or_create(UserID=self.user_tutor)
        self.language = Language.objects.create(name="Python")
        self.tutor.languages.add(self.language)

        self.invoice = Invoice.objects.create(
            student= self.student,
            tutor= self.tutor,
            total_amount=Decimal('100.00'),
            paid=True,
            approved=True,
            date_issued="2024-12-01",
            date_paid="2024-12-01"
        )

        self.lesson = Lesson.objects.create(
            tutor=self.tutor,
            student=self.student,
            language=self.language,
            invoice=self.invoice,
            time="10:00",
            date="2024-12-01",
            venue="BH 6.02",
            duration=60,
            frequency="once a week",
            term="sept-christmas"
        )

        TutorAvailability.objects.create(
            tutor=self.tutor,
            start_time="09:00",
            end_time="18:00",
            day="2024-12-01",
            availability_status='available',
            action='edit'
        )

    def test_dashboard_as_admin(self):
        """Test the dashboard view for an admin user"""
        
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        
        self.assertIn('users', response.context)
        self.assertIn('student_data', response.context)
        self.assertIn('tutor_data', response.context)
        self.assertIn('lessons_data', response.context)
        self.assertIn('invoices_data', response.context)

        self.assertTrue(len(response.context['users']) > 0)
        self.assertTrue(len(response.context['student_data']) > 0)
        self.assertTrue(len(response.context['tutor_data']) > 0)
        self.assertTrue(len(response.context['lessons_data']) > 0)
        self.assertTrue(len(response.context['invoices_data']) > 0)

    def test_dashboard_with_search_as_admin(self):
        """Test the dashboard view for an admin user with search query"""
        
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'search': '@jane_smith'})

        self.assertEqual(response.status_code, 200)
        
        # Ensure only the student user is filtered
        self.assertEqual(len(response.context['users']), 1)
        self.assertEqual(response.context['users'][0].username, '@jane_smith')

    def test_dashboard_as_tutor(self):
        """Test the dashboard view for a tutor user"""
        
        self.client.login(username='@john_doe', password='password123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)

        self.assertIn('lessons', response.context)
        self.assertIn('availabilities', response.context)

        # Ensure tutor's lessons and availability are included
        self.assertTrue(len(response.context['lessons']) > 0)
        self.assertTrue(len(response.context['availabilities']) > 0)

    def test_dashboard_as_student(self):
        """Test the dashboard view for a student user"""
        
        self.client.login(username='@jane_smith', password='password123')
        
        # Scenario where the student has lessons and an invoice
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('lessons', response.context)
        self.assertIn('invoice', response.context)

        # Ensure the student has lessons and an invoice
        self.assertTrue(len(response.context['lessons']) > 0)
        self.assertEqual(response.context['invoice'].total_amount, 100.0)

    def test_dashboard_with_action_filter_unallocated(self):
        """Test the dashboard with action filter for 'unallocated' requests"""
        
        # Create unallocated lesson requests (just an example, modify based on your logic)
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'action_filter': 'unallocated'})

        self.assertEqual(response.status_code, 200)

        # Ensure only unallocated data is included
        self.assertIn('student_data', response.context)
        self.assertTrue(all(data['unallocated_request'] for data in response.context['student_data']))

    def test_dashboard_with_action_filter_allocated(self):
        """Test the dashboard with action filter for 'allocated' lessons"""
        
        # Create allocated lesson requests (just an example, modify based on your logic)
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'action_filter': 'allocated'})

        self.assertEqual(response.status_code, 200)

        # Ensure only allocated data is included
        self.assertIn('student_data', response.context)
        self.assertTrue(all(data['allocated_lesson'] for data in response.context['student_data']))

    def test_dashboard_with_action_filter_no_actions(self):
        """Test the dashboard with action filter for 'no_actions'"""
        
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'action_filter': 'no_actions'})

        self.assertEqual(response.status_code, 200)

        # Ensure only students with no actions are included
        self.assertIn('student_data', response.context)
        self.assertTrue(all(not data['unallocated_request'] and not data['allocated_lesson'] for data in response.context['student_data']))

    def test_dashboard_with_sort_query_as_admin(self):
        """Test the dashboard view for an admin with sorting"""
        
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'sort_query': 'tutor'})

        self.assertEqual(response.status_code, 200)

        # Ensure the users are filtered by the 'tutor' role
        self.assertEqual(len(response.context['users']), 1)
        self.assertEqual(response.context['users'][0].role, 'tutor')

    def test_dashboard_with_invalid_tab(self):
        """Test the dashboard view with an invalid 'tab' parameter"""
        
        self.client.login(username='@admin_user', password='adminpassword')
        response = self.client.get(reverse('dashboard'), {'tab': 'invalid_tab'})

        self.assertEqual(response.status_code, 200)
        
        # Ensure that 'tab' is still passed into the context
        self.assertEqual(response.context['tab'], 'invalid_tab')