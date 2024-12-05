"""Unit tests of the log in form."""
from django import forms
from django.test import TestCase
from tutorials.forms import LogInForm
from tutorials.models import User

class LogInFormTestCase(TestCase):
    """Unit tests of the log in form."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets up the form input for tests."""
        self.form_input = {'username': '@janedoe', 'password': 'Password123'}

    def test_form_contains_required_fields(self):
        """Tests that the form contains the required fields."""
        form = LogInForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)
        password_field = form.fields['password']
        self.assertTrue(isinstance(password_field.widget,forms.PasswordInput))

    def test_form_accepts_valid_input(self):
        """Tests that the form accepts valid input."""
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_rejects_blank_username(self):
        """Tests that the form rejects an empty username."""
        self.form_input['username'] = ''
        form = LogInForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_rejects_blank_password(self):
        """Tests that the form rejects an empty password."""
        self.form_input['password'] = ''
        form = LogInForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_accepts_incorrect_username(self):
        """Tests that the form accepts a wrong username."""
        self.form_input['username'] = 'ja'
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_accepts_incorrect_password(self):
        """Tests that the form accepts a wrong password."""
        self.form_input['password'] = 'pwd'
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_can_authenticate_valid_user(self):
        """"Tests that the form validate a valid user."""
        fixture = User.objects.get(username='@johndoe')
        form_input = {'username': '@johndoe', 'password': 'Password123'}
        form = LogInForm(data=form_input)
        user = form.get_user()
        self.assertEqual(user, fixture)

    def test_invalid_credentials_do_not_authenticate(self):
        """Tests that the form rejects a user with the wrong credentials."""
        form_input = {'username': '@johndoe', 'password': 'WrongPassword123'}
        form = LogInForm(data=form_input)
        user = form.get_user()
        self.assertEqual(user, None)

    def test_blank_password_does_not_authenticate(self):
        """Tests that an empty password is rejected."""
        form_input = {'username': '@johndoe', 'password': ''}
        form = LogInForm(data=form_input)
        user = form.get_user()
        self.assertEqual(user, None)

    def test_blank_username_does_not_authenticate(self):
        """Tests that an empty username is rejected."""
        form_input = {'username': '', 'password': 'Password123'}
        form = LogInForm(data=form_input)
        user = form.get_user()
        self.assertEqual(user, None)
