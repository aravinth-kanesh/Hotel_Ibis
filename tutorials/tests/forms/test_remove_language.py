from django.test import TestCase
from tutorials.models import Tutor, Language, User
from tutorials.forms import RemoveLanguageForm

class RemoveLanguageFormTestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(
            username="tutor_user",
            email="tutor.user@example.org",
            password="Password123",
            role="tutor",
        )
        Tutor.objects.filter(UserID=self.tutor_user).delete()
        self.tutor = Tutor.objects.create(UserID=self.tutor_user)
        
        self.language = Language.objects.create(name="Python")
        self.language1 = Language.objects.create(name="Scala")
        self.other_language = Language.objects.create(name="Java")

        self.tutor.languages.add(self.language)

    def test_valid_language_removal(self):
        form_data = {'language_id': self.language.id}
        form = RemoveLanguageForm(data=form_data, tutor=self.tutor)
        self.assertTrue(form.is_valid())
        language = form.cleaned_data['language_id']
        self.assertEqual(language, self.language)

    def test_invalid_language_id(self):
        form_data = {'language_id': 999}  # Non-existent language
        form = RemoveLanguageForm(data=form_data, tutor=self.tutor)
        self.assertFalse(form.is_valid())
        self.assertIn("The selected language does not exist.", form.errors['language_id'])

    def test_unauthorized_language_removal(self):
        form_data = {'language_id': self.language1.id}  # Language not associated with the tutor
        form = RemoveLanguageForm(data=form_data, tutor=self.tutor)
        self.assertFalse(form.is_valid())
        self.assertIn("You do not have permission to remove this language.", form.errors['language_id'])