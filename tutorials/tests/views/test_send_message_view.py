from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Message
from tutorials.forms import MessageForm

class SendMessageViewTests(TestCase):
    fixtures = ['user_fixtures.json']  # Assuming the fixture file is named `user_fixtures.json`

    def setUp(self):
        # Load users from the fixture
        self.sender = get_user_model().objects.get(pk=3)  # User with pk=3 from the fixture
        self.recipient = get_user_model().objects.create_user(
            username="recipient",
            password="recipientpassword",
            email="recipient@example.com"
        )

        # Log in as the sender
        self.client = Client()
        self.client.login(username=self.sender.username, password="pbkdf2_sha256$260000$4BNvFuAWoTT1XVU8D6hCay$KqDCG+bHl8TwYcvA60SGhOMluAheVOnF1PMz0wClilc=")

        # Set the URL for the view
        self.url = reverse("send_message")

    def test_get_request_form(self):
        """Test that the form renders correctly for logged-in users."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "send_message.html")
        self.assertIsInstance(response.context["form"], MessageForm)

    def test_redirect_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {
            "recipient": self.recipient.id,
            "subject": "Test Message",
            "content": "This is a test message.",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Expect a redirect on success
        self.assertRedirects(response, reverse("all_messages"))  # Ensure it redirects to the success URL
        self.assertTrue(Message.objects.filter(subject="Test Message").exists())
        message = Message.objects.get(subject="Test Message")
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.recipient, self.recipient)

    def test_form_submission_invalid(self):
        """Test form submission with invalid data."""
        data = {
            "recipient": "",
            "subject": "",
            "content": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Stays on the same page
        self.assertFormError(response, "form", "recipient", "This field is required.")
        self.assertFormError(response, "form", "subject", "This field is required.")
        self.assertFormError(response, "form", "content", "This field is required.")

    def test_reply_message_context(self):
        """Test that the reply message is passed in the context when reply_id is provided."""
        reply_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Original Message",
            content="This is the original message."
        )
        url_with_reply = reverse("send_message", kwargs={"reply_id": reply_message.id})
        response = self.client.get(url_with_reply)
        self.assertEqual(response.status_code, 200)
        self.assertIn("reply_message", response.context)
        self.assertEqual(response.context["reply_message"], reply_message)

    def test_form_submission_with_reply(self):
        """Test that a reply message is correctly linked to the original message."""
        original_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Original Message",
            content="This is the original message."
        )
        url_with_reply = reverse("send_message", kwargs={"reply_id": original_message.id})
        data = {
            "recipient": self.recipient.id,
            "subject": "Re: Original Message",
            "content": "This is a reply to the original message.",
        }
        response = self.client.post(url_with_reply, data)
        self.assertEqual(response.status_code, 302)
        reply_message = Message.objects.get(subject="Re: Original Message")
        self.assertEqual(reply_message.previous_message, original_message)
