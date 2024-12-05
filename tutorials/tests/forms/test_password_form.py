from django.contrib.auth.hashers import check_password
from django.test import TestCase
from tutorials.models import User
from tutorials.forms import PasswordForm

class PasswordFormTestCase(TestCase):

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets up the user and initial form."""
        self.user = User.objects.get(username='@johndoe')
        self.form_input = {
            'password': 'Password123',
            'new_password': 'NewPassword123',
            'password_confirmation': 'NewPassword123',
        }

    def test_form_has_necessary_fields(self):
        """Tests that the form contains the required fields."""
        form = PasswordForm(user=self.user)
        self.assertIn('password', form.fields)
        self.assertIn('new_password', form.fields)
        self.assertIn('password_confirmation', form.fields)

    def test_valid_form(self):
        """Tests that the form is valid with the right input."""
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_password_must_contain_uppercase_character(self):
        """Checks the new password has at least one capital letter."""
        self.form_input['new_password'] = 'password123'
        self.form_input['password_confirmation'] = 'password123'
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_lowercase_character(self):
        """Checks the new password has at least one lowercase letter."""
        self.form_input['new_password'] = 'PASSWORD123'
        self.form_input['password_confirmation'] = 'PASSWORD123'
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_number(self):
        """Checks the new password has at least one number."""
        self.form_input['new_password'] = 'PasswordABC'
        self.form_input['password_confirmation'] = 'PasswordABC'
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_new_password_and_password_confirmation_are_identical(self):
        """Checks that the password and password confirmation match."""
        self.form_input['password_confirmation'] = 'WrongPassword123'
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_be_valid(self):
        """Checks that the password is correct."""
        self.form_input['password'] = 'WrongPassword123'
        form = PasswordForm(user=self.user, data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_must_contain_user(self):
        """Checks that the form includes a valid user instance."""
        form = PasswordForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_save_form_changes_password(self):
        """Checks that the form changes the user's password."""
        form = PasswordForm(user=self.user, data=self.form_input)
        form.full_clean()
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(check_password('Password123', self.user.password))
        self.assertTrue(check_password('NewPassword123', self.user.password))

    def test_save_userless_form(self):
        """Checks that the form does not save if no user is provided."""
        form = PasswordForm(user=None, data=self.form_input)
        form.full_clean()
        result = form.save()
        self.assertFalse(result)