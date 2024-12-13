from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Message
from tutorials.views import MessageDetailView

class MessageDetailViewTests(TestCase):
    def setUp(self):
        self.sender = get_user_model().objects.create_user(
            username="sender",
            password="password123",
            email="sender@example.com"
        )

        self.recipient = get_user_model().objects.create_user(
            username="recipient",
            password="password123",
            email="recipient@example.com"
        )

        self.other_user = get_user_model().objects.create_user(
            username="other_user",
            password="password123",
            email="other_user@example.com"
        )

        self.original_message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Original Message",
            content="This is the original message."
        )
        self.url = reverse("message_detail", kwargs={"pk": self.original_message.id})

        self.reply_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Re: Original Message",
            content="This is a reply to the original message.",
            previous_message=self.original_message
        )

        self.original_message.reply = self.reply_message
        self.original_message.save()

        # Create a message without saving it to the database (so no ID)
        self.message_no_id = Message(
            sender=self.sender,
            recipient=self.recipient,
            subject="No ID Message",
            content="This message has no ID yet."
        )

        self.client = Client()

    def test_redirect_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to the login page."""
        url = reverse("message_detail", kwargs={"pk": self.original_message.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"/log_in/?next={url}")

    def test_access_unauthorized_user(self):
        """Test that an unauthorized user cannot view the message."""
        self.client.login(username="other_user", password="password123")
        url = reverse("message_detail", kwargs={"pk": self.original_message.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_context_includes_previous_and_next_message(self):
        """Test that the context includes previous and next message."""
        self.client.login(username="recipient", password="password123")
        url = reverse("message_detail", kwargs={"pk": self.reply_message.pk})
        response = self.client.get(url)
        self.assertEqual(response.context["previous_message"], self.original_message)
        self.assertIsNone(response.context["next_message"])

    def test_nonexistent_message(self):
        """Test that a non-existent message raises 404."""
        self.client.login(username="sender", password="password123")
        url = reverse("message_detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_message_detail_url(self):
        """Ensure the URL is correct."""
        url = reverse("message_detail", kwargs={"pk": self.original_message.id})
        self.assertEqual(url, f"/messages/{self.original_message.id}/")