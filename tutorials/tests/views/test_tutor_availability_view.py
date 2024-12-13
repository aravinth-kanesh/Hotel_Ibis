from datetime import date, datetime, time
from django.test import TestCase
from django.urls import reverse
from tutorials.forms import TutorAvailabilityForm
from tutorials.models import User, Tutor, Language, Student, TutorAvailability
from django.contrib.messages import get_messages
from django.db.models.functions import Lower

class tutorAvailabiltyViewTestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        self.user = User.objects.create_user(
            username="no_tutor_user",
            email="notutor@example.com",
            password="Password123"
        )
        # Assuming 'Tutor' model has a OneToOne link to User
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)

        self.availability1 = TutorAvailability.objects.create(
            tutor=self.tutor,
            day=date(2024, 12, 12),
            start_time=time(9, 0),
            end_time=time(12, 0),
            availability_status='available',
        )

        self.form_input = {
            'tutor':self.tutor.id,
            'day': '2024-12-14',
            'start_time': '10:00',
            'end_time': '12:00',
            'availability_status': 'available',
            'repeat': 'once',
        }

        self.form_input_no_tutor = {
            'day': '2024-12-14',
            'start_time': '10:00',
            'end_time': '12:00',
            'availability_status': 'available',
            'repeat': 'once',
        }

        self.updated_form_input = {
            'tutor': self.tutor.id,  # Keep the same tutor
            'day': '2024-12-15',  # Change the day
            'start_time': '14:00',  # Change the start time
            'end_time': '16:00',  # Change the end time
            'availability_status': 'not_available',  # Change the status
            'repeat': 'weekly'
        }

        self.form_input_overlapping = {
            'tutor': self.tutor.id,  # Keep the same tutor
            'day': '2024-12-12',  # Change the day
            'start_time': '8:00',  # Change the start time
            'end_time': '11:00',  # Change the end time
            'availability_status': 'available',  # Change the status
            'repeat': 'weekly'
        }

        self.form_input_invalid = {
            'tutor': self.tutor.id,  # Keep the same tutor
            'day': '2024-12-12',  # Change the day
            'start_time': '8:00',  # Change the start time
            'end_time': '7:00',  # Change the end time
            'availability_status': 'available',  # Change the status
            'repeat': 'weekly'
        }


        self.client.login(username="tutor_user", password="Password123")
        self.url = reverse('tutor_availability_request')
        

    def test_get_availability(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor_availability_request.html')
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertTrue(isinstance(form, TutorAvailabilityForm))
        self.assertFalse(form.is_bound)

    def test_tutor_not_found(self):
        Tutor.objects.all().delete()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_get_edit_valid(self):
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=edit'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsInstance(form, TutorAvailabilityForm)
        self.assertEqual(form.instance, self.availability1, "Form should be bound to the correct availability instance.")
        self.assertEqual(form.instance.day, self.availability1.day)
        self.assertEqual(form.instance.start_time, self.availability1.start_time)
        self.assertEqual(form.instance.end_time, self.availability1.end_time)
        self.assertEqual(form.instance.availability_status, self.availability1.availability_status)
        self.assertEqual(form.instance.tutor.id, self.availability1.tutor.id)

    def test_get_delete_valid(self):
        before_count = TutorAvailability.objects.count()
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=delete'
        response = self.client.get(url)
        expected_redirect_url = f"{reverse('dashboard')}?tab=availability"
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)
        after_count = TutorAvailability.objects.count()
        self.assertEqual(after_count, before_count-1)
        self.assertFalse(TutorAvailability.objects.filter(id=self.availability1.id).exists(), "Availability should be deleted after the delete action.")

    def test_get_action_invalid(self):
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=invalid'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid action", status_code=400)

    def test_post_new_availability(self):
        before_count = TutorAvailability.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        after_count = TutorAvailability.objects.count()
        self.assertEqual(after_count, before_count+1)
        self.assertTrue(TutorAvailability.objects.filter(
            tutor=self.tutor,
            day='2024-12-14',
            start_time='10:00',
            end_time='12:00',
            availability_status='available'
        ).exists(), "New availability should be created.")

    def test_post_new_availabilility_invalid_data(self):
        self.form_input['tutor'] = ''
        before_count = TutorAvailability.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        after_count = TutorAvailability.objects.count()
        self.assertEqual(after_count, before_count)

    def test_post_edit_availability_valid(self):
        before_count = TutorAvailability.objects.count()
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=edit'
        response = self.client.post(url, self.updated_form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, f"{reverse('dashboard')}?tab=availability")
        self.availability1.refresh_from_db()
        after_count = TutorAvailability.objects.count()
        self.assertEqual(after_count, before_count, "No new availability should be created during edit.")
        self.assertEqual(self.availability1.day,datetime.strptime(self.updated_form_input['day'], '%Y-%m-%d').date())
        self.assertEqual(self.availability1.start_time.strftime('%H:%M'),self.updated_form_input['start_time'])
        self.assertEqual(self.availability1.end_time.strftime('%H:%M'),self.updated_form_input['end_time'])
        self.assertEqual(self.availability1.availability_status, self.updated_form_input['availability_status'])
        self.assertEqual(self.availability1.tutor.id, self.updated_form_input['tutor'])

    def test_post_overlapping(self):
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=edit'
        response = self.client.post(url, self.form_input_overlapping, follow=True)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid(), "Form should be invalid due to overlapping availability")
        self.assertIn('__all__', form.errors, "This time slot overlaps with an existing availability.")
        self.assertIn("This time slot overlaps with an existing availability.",form.errors['__all__'])

    def test_post_times_invalid(self):
        before_count = TutorAvailability.objects.count()
        response = self.client.post(self.url, self.form_input_invalid, follow=True)
        self.assertEqual(response.status_code, 200)
        after_count = TutorAvailability.objects.count()
        self.assertEqual(after_count, before_count)
        form = response.context['form']
        self.assertFalse(form.is_valid(), "Form should be invalid due to time selection")
        self.assertIn('__all__', form.errors, 'Start time must be earlier than end time.')
        self.assertIn('Start time must be before end time.',form.errors['__all__'])

    def test_post_times_invalid_edit(self):
        url = reverse('edit_tutor_availability', kwargs={'availability_id': self.availability1.id}) + '?action=edit'
        response = self.client.post(self.url, self.form_input_invalid, follow=True)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid(), "Form should be invalid due to time selection")
        self.assertIn('__all__', form.errors, 'Start time must be earlier than end time.')
        self.assertIn('Start time must be before end time.',form.errors['__all__'])

    def test_post_tutor_does_not_exist(self):
        self.client.logout()
        self.client.login(username="no_tutor_user", password="Password123")
        response = self.client.post(self.url, self.form_input_no_tutor, follow=True)
        expected_redirect_url = f"{reverse('dashboard')}?tab=availability"
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)



        


        








    




        



        




        
        

