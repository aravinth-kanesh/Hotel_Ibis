from django.test import TestCase
from django.urls import reverse
from tutorials.forms import TutorLanguageForm, RemoveLanguageForm
from tutorials.models import User, Tutor, Language, Student
from django.contrib.messages import get_messages

class tutorLanguageRequestViewTestCase(TestCase):
    """creating a test case to test language forms for tutors"""
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        # Assuming 'Tutor' model has a OneToOne link to User
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)

        # Create non-tutor user
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student.user@example.org",
            password="Password123",
            role="student",
        )

        Student.objects.filter(UserID=self.student_user).delete()
        Student.objects.create(UserID=self.student_user)

        Language.objects.all().delete()
        self.pythonLan = Language.objects.create(name="Python")
        Language.objects.create(name="Java")
        Language.objects.create(name="c++")
        Language.objects.create(name="c#")
        self.language = Language.objects.create(name="SQL")

        self.tutor.languages.add(self.pythonLan)
        self.tutor.languages.add(self.language)

        # Form input setup
        self.form_input = {
            'add_language': 'Add',
            'language_name': 'scala'
        }

        self.form_input2 = {
            'add_language': 'Add',
            'language_name': 'java'
        }

        self.form_input3 = {
            'add_language': 'Add',
            'language_name': ''
        }

        self.form_input4 = {
            'query' : ''
        }

        self.form_input5 = {
            'remove_language': 'Remove',
            'language_id' : self.language.id
        }

        # Log in as student_user by default (if this is the intent for all tests)
        self.client.login(username="tutor_user", password="Password123")

        # Correct the URL setup if necessary
        self.url = reverse('manage_languages')  # Verify the correct URL name

    def test_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        login_url = f"{reverse('log_in')}?next={self.url}"
        self.assertRedirects(response, login_url, status_code=302, target_status_code=200)

    def test_tutor_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
    def test_non_tutor_access(self):
        self.client.login(username="student_user", password="Password123")
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/dashboard/', status_code=302, target_status_code=200)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("You must be a tutor to manage languages.", [msg.message for msg in messages])

    def test_get_manage_language(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manage_languages.html')
        self.assertIn('add_form', response.context)
        form = response.context['add_form']
        self.assertTrue(isinstance(form, TutorLanguageForm))
        self.assertFalse(form.is_bound)

    def test_add_existing_language_query(self):
        self.assertEqual(Language.objects.filter(name='python').count(), 1)
        response = self.client.get(self.url, {'query': 'python'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Language.objects.filter(name='python').exists())
        messages = list(get_messages(response.wsgi_request))
        expected_message = "Language 'python' already exists and has been added to your languages."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected info message not found.")
        
    def test_add_new_language_query(self):
        before_count = Language.objects.count()
        query_language = 'ruby'
        response = self.client.get(self.url, {'query': query_language})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Language.objects.filter(name='ruby').exists())
        messages = list(get_messages(response.wsgi_request))
        expected_message = "New language 'ruby' created and added to your languages."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected info message not found.")
        after_count = Language.objects.count()
        self.assertTrue(after_count, before_count+1)
    
    def test_add_new_language_post(self):
        before_count = Language.objects.count()
        self.assertFalse(Language.objects.filter(name='scala').exists())
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Language.objects.filter(name='scala').exists(), "Language should be added.")
        after_count = Language.objects.count()
        self.assertTrue(after_count, before_count+1)
        self.assertTrue(self.tutor.languages.filter(name='scala').exists())
        messages = list(get_messages(response.wsgi_request))
        expected_message = "New language 'scala' created and added to your languages."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected success message not found.")

    def test_add_existing_language_post(self):
        response = self.client.post(self.url, self.form_input2, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Language.objects.filter(name='java'))
        self.assertEqual(Language.objects.filter(name='java').count(), 1, "No duplicate should be created.")
        self.assertTrue(self.tutor.languages.filter(name='java').exists())
        messages = list(get_messages(response.wsgi_request))
        expected_message = "Language 'java' added to your languages."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected success message not found.")

    def test_invalid_language_post(self):
        before_count = self.tutor.languages.all().count()
        response = self.client.post(self.url, self.form_input3, follow=True)
        after_count = self.tutor.languages.all().count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        expected_message = "Failed to add the language. Please try again."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected error message not found.")

    def test_empty_form_submission(self):
    # Sending empty data, expecting to handle this case specifically in your view or form logic.
        response = self.client.get(self.url, {'query' : ''})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        expected_message = "No input provided. Please enter a search term."
        self.assertTrue(any(expected_message in str(msg) for msg in messages), "Expected error message not found.")

    def test_close_match_query_short_form(self):
        response = self.client.get(self.url, {'query': 'c'})
        self.assertEqual(response.status_code, 200)
        search_results = response.context['search_results']
        expected_matches = ['c++', 'c#']
        actual_matches = [lang.name for lang in search_results]
        self.assertTrue(all(item in actual_matches for item in expected_matches), "All close matches should be included in the results.")

    def test_remove_language(self):
        response = self.client.post(self.url, self.form_input5, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        expected_message = f"{self.language.name} has been deleted as no tutors teach it anymore."
        self.assertTrue(any(expected_message in str(msg) for msg in messages))
        self.assertFalse(self.tutor.languages.filter(id=self.language.id).exists())

    def test_remove_language_invalid(self):
        form_data = {
            'remove_language': 'Remove',
            'language_id': 999}  
        form = RemoveLanguageForm(data=form_data, tutor=self.tutor)
        self.assertFalse(form.is_valid())
        self.assertIn('language_id', form.errors)
        self.assertEqual(form.errors['language_id'][0], "The selected language does not exist.")
        response = self.client.post(self.url, form_data, follow=True)
        messages = list(get_messages(response.wsgi_request))
        expected_message = "An error occurred while removing the language."
        self.assertTrue(any(expected_message in str(msg) for msg in messages))

    def test_invalid_form(self):
        form_data = {'query': '', 'existing_language': 99}
        form = TutorLanguageForm(data=form_data)
        response = self.client.post(self.url, form_data, follow=True)
        self.assertFalse(form.is_valid())

    
    

    

    


