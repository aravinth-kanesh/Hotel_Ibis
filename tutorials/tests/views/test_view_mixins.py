from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from tutorials.views import LoginProhibitedMixin

class LoginProhibitedMixinTestCase(TestCase):
	def test_login_prohibited_throws_exception_when_not_configured(self):
		"""Tests that the LoginProhibitedMixin raises an exception if not configured properly."""
		mixin = LoginProhibitedMixin()
		with self.assertRaises(ImproperlyConfigured):
			mixin.get_redirect_when_logged_in_url()