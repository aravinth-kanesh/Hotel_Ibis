from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import Http404
from .models import Message

class MessageDetailViewTests(TestCase):
    fixtures = ['user_fixtures.json']  # Assuming the fixture file is named `user_fixtures.json`

    def setUp(self):
        # Load users from the fixture
        self.sender = get_user_model().objects.get(pk=3)  # User with pk=3 from the fixture
        self.recipient = get_user_model().objects.create_user(
            username="recipient",
            password="recipientpassword",
            email="recipient@example.com"
        )

        # Create test messages
        self.original_message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Original Message",
            content="This is the original message."
        )
        self.reply_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Re: Original Message",
            content="This is a reply to the original message.",
            previous_message=self.original_message
        )
        self.original_message.reply = self.reply_message
        self.original_message.save()

        # Log in as the sender
        self.client = Client()
        self.client.login(username=self.sender.username, password="pbkdf2_sha256$260000$4BNvFuAWoTT1XVU8D6hCay$KqDCG+bHl8TwYcvA60SGhOMluAheVOnF1PMz0wClilc=")

        # Set the URL for the view
        self.url = reverse("message_detail", kwargs={"pk": self.original_message.id})

    def test_redirect_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_access_authorized_user(self):
        """Test that an authorized user can view the message."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "message_detail.html")
        self.assertEqual(response.context["message"], self.original_message)

    def test_access_unauthorized_user(self):
        """Test that an unauthorized user cannot view the message."""
        other_user = get_user_model().objects.create_user(
            username="unauthorized",
            password="unauthorizedpassword",
            email="unauthorized@example.com"
        )
        self.client.login(username="unauthorized", password="unauthorizedpassword")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)  # Forbidden for unauthorized access

    def test_context_includes_previous_and_next_message(self):
        """Test that the context includes previous and next message."""
        response = self.client.get(self.url)
        self.assertEqual(response.context["previous_message"], None)
        self.assertEqual(response.context["next_message"], self.reply_message)

    def test_context_includes_reply_url(self):
        """Test that the context includes the reply URL."""
        response = self.client.get(self.url)
        self.assertEqual(response.context["reply_url"], reverse("reply_message", kwargs={"reply_id": self.original_message.id}))

    def test_nonexistent_message(self):
        """Test that a non-existent message raises 404."""
        nonexistent_url = reverse("message_detail", kwargs={"pk": 999})
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)
