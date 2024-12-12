from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Message

class AllMessagesViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']  # Assuming the fixture file is named `user_fixtures.json`

    def setUp(self):
        # Load users from the fixture
        self.user = get_user_model().objects.get(pk=3)  # User with pk=3 from the fixture
        self.other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="otherpassword",
            email="otheruser@example.com"
        )

        # Create test messages
        self.sent_message = Message.objects.create(
            sender=self.user,
            recipient=self.other_user,
            subject="Sent Message",
            content="This is a sent message."
        )
        self.received_message = Message.objects.create(
            sender=self.other_user,
            recipient=self.user,
            subject="Received Message",
            content="This is a received message."
        )

        # Log in as the user
        self.client = Client()
        self.client.login(username=self.user.username, password="Password123")

        # Set the URL for the view
        self.url = reverse("all_messages")

    def test_redirect_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"login/?next={self.url}")

    def test_view_renders_correctly(self):
        """Test that the view renders with the correct template and context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "all_messages.html")
        self.assertIn("sent_messages", response.context)
        self.assertIn("received_messages", response.context)

    def test_sent_messages_context(self):
        """Test that the sent messages are included in the context."""
        response = self.client.get(self.url)
        sent_messages = response.context["sent_messages"]
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0], self.sent_message)
        self.assertEqual(sent_messages[0].subject, "Sent Message")

    def test_received_messages_context(self):
        """Test that the received messages are included in the context."""
        response = self.client.get(self.url)
        received_messages = response.context["received_messages"]
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0], self.received_message)
        self.assertEqual(received_messages[0].subject, "Received Message")

    def test_no_messages_for_user(self):
        """Test that the context contains no messages when the user has none."""
        new_user = get_user_model().objects.create_user(
            username="newuser",
            password="newpassword123",
            email="newuser@example.com"
        )
        self.client.login(username="newuser", password="newpassword123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["sent_messages"], [])
        self.assertQuerysetEqual(response.context["received_messages"], [])
