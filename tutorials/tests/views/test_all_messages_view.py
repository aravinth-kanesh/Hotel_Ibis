"""Tests of the all messages view."""
from django.test import TestCase
from django.urls import reverse
from tutorials.models import User, Message

class AllMessagesViewTestCase(TestCase):
    """Tests of the AllMessagesView."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets up test environment."""
        self.user = User.objects.get(username='@johndoe')
        self.recipient = User.objects.get(username='@janedoe')
        self.sent_message = Message.objects.create(
            sender=self.user,
            recipient=self.recipient,
            subject='Sent Message',
            content='This is a test message.'
        )
        self.received_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.user,
            subject='Received Message',
            content='This is a test message.'
        )
        self.url = reverse('all_messages')

    def test_all_messages_url(self):
        """Ensure the URL is correct."""
        self.assertEqual(self.url, '/messages/')

    def test_get_all_messages(self):
        """Ensure the page loads correctly and the correct template is used."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_messages.html')
        self.assertContains(response, 'Your Messages')
        self.assertContains(response, self.sent_message.subject)
        self.assertContains(response, self.received_message.subject)
        self.assertContains(response, self.sent_message.sender.username)
        self.assertContains(response, self.received_message.sender.username)
        self.assertContains(response, self.sent_message.recipient.username)
        self.assertContains(response, self.received_message.recipient.username)

    def test_get_all_messages_redirects_when_not_logged_in(self):
        """Ensure a user that has not logged in is redirected to login."""
        response = self.client.get(self.url)
        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={self.url}')

    def test_get_all_messages_logged_in(self):
        """Ensure a user that has logged in can view the page."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sent_message.subject)
        self.assertContains(response, self.received_message.subject)

    def test_view_received_messages_tab(self):
        """Ensure the received messages tab displays the correct messages."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, self.received_message.subject)
        self.assertContains(response, self.received_message.sender.username)
        self.assertContains(response, self.received_message.recipient.username)

    def test_view_sent_messages_tab(self):
        """Ensure the sent messages tab displays the correct messages."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, self.sent_message.subject)
        self.assertContains(response, self.sent_message.sender.username)
        self.assertContains(response, self.sent_message.recipient.username)

    def test_no_received_messages(self):
        """Ensure that the 'No received messages' message is displayed when no received messages exist."""
        self.client.login(username=self.user.username, password="Password123")
        self.received_message.delete()
        response = self.client.get(self.url)
        self.assertContains(response, 'No received messages.')

    def test_no_sent_messages(self):
        """Ensure that the 'No sent messages' message is displayed when no sent messages exist."""
        self.client.login(username=self.user.username, password="Password123")
        self.sent_message.delete()
        response = self.client.get(self.url)
        self.assertContains(response, 'No sent messages.')

    def test_send_message_button(self):
        """Ensure the send message button directs the user to the correct send message URL."""
        send_message_url = reverse('send_message')
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, f'href="{send_message_url}"')