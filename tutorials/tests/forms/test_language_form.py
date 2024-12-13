from django.test import TestCase
from django.urls import reverse
from tutorials.forms import TutorLanguageForm
from tutorials.models import User, Tutor, Language

class tutorLanguageFormTestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)

        self.language = Language.objects.create(name="Scala")
        self.language1 = Language.objects.create(name="Python")
        self.language2 = Language.objects.create(name="Java")

        self.client.login(username="tutor_user", password="Password123")
        self.url = reverse('manage_languages')

    def test_valid_existing_language(self):
        form_data = {'query': '', 'existing_language': self.language1.id}
        form = TutorLanguageForm(data=form_data)
        self.assertTrue(form.is_valid())
        language = form.save_or_create_language()
        self.assertEqual(language, self.language1)
        self.assertTrue(Language.objects.filter(name='python').exists())

    def test_valid_query_creates_new_language(self):
        before_count = Language.objects.count()
        form_data = {'query': 'c++', 'existing_language': ''}
        form = TutorLanguageForm(data=form_data)
        self.assertTrue(form.is_valid())
        language = form.save_or_create_language()
        after_count = Language.objects.count()
        self.assertEquals(before_count+1, after_count)
        self.assertEqual(language.name, 'c++')
        self.assertTrue(Language.objects.filter(name='c++').exists())
        self.assertTrue(Language.objects.filter(name='python').exists())

    def test_invalid_no_input(self):
        form_data = {'query': '', 'existing_language': ''}
        form = TutorLanguageForm(data=form_data)
        self.assertTrue(form.is_valid())  # Form is valid, but save_or_create_language() returns None
        language = form.save_or_create_language()
        self.assertIsNone(language)

    def test_existing_language_filtered_with_initial_query(self):
        form = TutorLanguageForm(initial_query="ja")
        queryset = form.fields['existing_language'].queryset
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.language2, queryset)

    def test_existing_language_case_insensitive_filter(self):
        form = TutorLanguageForm(initial_query="Scala")
        queryset = form.fields['existing_language'].queryset
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.language, queryset)

    def test_query_matches_existing_language(self):
        form_data = {'query': 'python', 'existing_language': ''}
        form = TutorLanguageForm(data=form_data)
        self.assertTrue(form.is_valid())
        language = form.save_or_create_language()
        self.assertEqual(language, self.language1)
        self.assertEqual(Language.objects.filter(name='python').count(), 1)

    def test_query_too_long(self):
        form_data = {'query': 'a' * 101, 'existing_language': ''}
        form = TutorLanguageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('query', form.errors)

    def test_query_with_whitespace(self):
        form_data = {'query': 'ruby ', 'existing_language': ''}
        form = TutorLanguageForm(data=form_data)
        self.assertTrue(form.is_valid())
        language = form.save_or_create_language()
        self.assertEqual(language.name, 'ruby')
        self.assertTrue(Language.objects.filter(name='ruby').exists())

    

