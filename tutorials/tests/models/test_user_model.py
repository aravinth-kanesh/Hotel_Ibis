"""Unit tests for the User model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tutorials.models import User

class UserModelTestCase(TestCase):
    """Unit tests for the User model."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json'
    ]

    GRAVATAR_URL = "https://www.gravatar.com/avatar/363c1b0cd64dadffb867236a00e62986"

    def setUp(self):
        """Sets up the test by loading a user from the fixture."""
        self.user = User.objects.get(username='@johndoe')

    def test_valid_user(self):
        """Tests that, with the correct fields, the user is valid."""
        self._assert_user_is_valid()

    def test_username_cannot_be_blank(self):
        """Tests that the username cannot be empty."""
        self.user.username = ''
        self._assert_user_is_invalid()

    def test_username_can_be_30_characters_long(self):
        """Tests that the username can be up to 30 characters."""
        self.user.username = '@' + 'x' * 29
        self._assert_user_is_valid()

    def test_username_cannot_be_over_30_characters_long(self):
        """Tests that the username cannot be over 30 characters."""
        self.user.username = '@' + 'x' * 30
        self._assert_user_is_invalid()

    def test_username_must_be_unique(self):
        """Tests that the username must be unique among the users."""
        second_user = User.objects.get(username='@janedoe')
        self.user.username = second_user.username
        self._assert_user_is_invalid()

    def test_username_must_start_with_at_symbol(self):
        """Tests that the username must start with an @ symbol."""
        self.user.username = 'johndoe'
        self._assert_user_is_invalid()

    def test_username_must_contain_only_alphanumericals_after_at(self):
        """Tests that the username must only contain alphumerical characters after the @."""
        self.user.username = '@john!doe'
        self._assert_user_is_invalid()

    def test_username_must_contain_at_least_3_alphanumericals_after_at(self):
        """Tests that the usenmae must have at least 3 alphanumerical characters after the @."""
        self.user.username = '@jo'
        self._assert_user_is_invalid()

    def test_username_may_contain_numbers(self):
        """Tests that the username can contain numbers."""
        self.user.username = '@j0hndoe2'
        self._assert_user_is_valid()

    def test_username_must_contain_only_one_at(self):
        """Tests that the username must only contain one @."""
        self.user.username = '@@johndoe'
        self._assert_user_is_invalid()


    def test_first_name_must_not_be_blank(self):
        """Tests that the first name cannot be empty."""
        self.user.first_name = ''
        self._assert_user_is_invalid()

    def test_first_name_need_not_be_unique(self):
        """Tests that the first name does not need to be unique."""
        second_user = User.objects.get(username='@janedoe')
        self.user.first_name = second_user.first_name
        self._assert_user_is_valid()

    def test_first_name_may_contain_50_characters(self):
        """Tests that the first name can be up to 50 characters."""
        self.user.first_name = 'x' * 50
        self._assert_user_is_valid()

    def test_first_name_must_not_contain_more_than_50_characters(self):
        """Tests that the first name cannot be longer than 50 characters."""
        self.user.first_name = 'x' * 51
        self._assert_user_is_invalid()


    def test_last_name_must_not_be_blank(self):
        """Tests that the last name cannot be empty."""
        self.user.last_name = ''
        self._assert_user_is_invalid()

    def test_last_name_need_not_be_unique(self):
        """Tests that the last name does not need to be unique."""
        second_user = User.objects.get(username='@janedoe')
        self.user.last_name = second_user.last_name
        self._assert_user_is_valid()

    def test_last_name_may_contain_50_characters(self):
        """Tests that the last name can be up to 50 characters."""
        self.user.last_name = 'x' * 50
        self._assert_user_is_valid()

    def test_last_name_must_not_contain_more_than_50_characters(self):
        """Tests that the last name cannot be longer than 50 characters."""
        self.user.last_name = 'x' * 51
        self._assert_user_is_invalid()


    def test_email_must_not_be_blank(self):
        """Tests that the email cannot be empty."""
        self.user.email = ''
        self._assert_user_is_invalid()

    def test_email_must_be_unique(self):
        """Tests that the email must be unique among users."""
        second_user = User.objects.get(username='@janedoe')
        self.user.email = second_user.email
        self._assert_user_is_invalid()

    def test_email_must_contain_username(self):
        """Tests that the email must contain the username."""
        self.user.email = '@example.org'
        self._assert_user_is_invalid()

    def test_email_must_contain_at_symbol(self):
        """Tests that the email must contain a @."""
        self.user.email = 'johndoe.example.org'
        self._assert_user_is_invalid()

    def test_email_must_contain_domain_name(self):
        """Tests that the email must contain a domain name."""
        self.user.email = 'johndoe@.org'
        self._assert_user_is_invalid()

    def test_email_must_contain_domain(self):
        """Tests that the email must contain a domain."""
        self.user.email = 'johndoe@example'
        self._assert_user_is_invalid()

    def test_email_must_not_contain_more_than_one_at(self):
        """Tests that the email cannot contain more than 1 @."""
        self.user.email = 'johndoe@@example.org'
        self._assert_user_is_invalid()


    def test_full_name_must_be_correct(self):
        """Tests that the full name returns correctly as first name + last name."""
        full_name = self.user.full_name()
        self.assertEqual(full_name, "John Doe")


    def test_default_gravatar(self):
        """Tests the default gravatar URL."""
        actual_gravatar_url = self.user.gravatar()
        expected_gravatar_url = self._gravatar_url(size=120)
        self.assertEqual(actual_gravatar_url, expected_gravatar_url)

    def test_custom_gravatar(self):
        """Tests the default gravatar URL with a size."""
        actual_gravatar_url = self.user.gravatar(size=100)
        expected_gravatar_url = self._gravatar_url(size=100)
        self.assertEqual(actual_gravatar_url, expected_gravatar_url)

    def test_mini_gravatar(self):
        """Tests the mini gravtar URL."""
        actual_gravatar_url = self.user.mini_gravatar()
        expected_gravatar_url = self._gravatar_url(size=60)
        self.assertEqual(actual_gravatar_url, expected_gravatar_url)

    def _gravatar_url(self, size):
        """Makes the expected gravatar URL."""
        gravatar_url = f"{UserModelTestCase.GRAVATAR_URL}?size={size}&default=mp"
        return gravatar_url


    def _assert_user_is_valid(self):
        """Asserts that the user is valid and does not return a ValidationError."""
        try:
            self.user.full_clean()
        except (ValidationError):
            self.fail('Test user should be valid')

    def _assert_user_is_invalid(self):
        """Asserts that the user is invalid and returns a ValidationError."""
        with self.assertRaises(ValidationError):
            self.user.full_clean()