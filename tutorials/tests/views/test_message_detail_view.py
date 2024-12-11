"""Tests of the message detail view."""
from django.test import TestCase
from django.urls import reverse
from tutorials.models import User, Message

class MessageDetailViewTestCase(TestCase):
    """Tests of the MessageDetailView."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        """Sets up test environment."""
        self.user = User.objects.get(username='@johndoe')
        self.recipient = User.objects.get(username='@janedoe')
        self.message = Message.objects.create(
            sender=self.user,
            recipient=self.recipient,
            subject='Test Message',
            content='This is a test message.'
        )
        self.url = reverse('message_detail', kwargs={'pk': self.message.id})

    def test_message_detail_url(self):
        """Ensure the URL is correct."""
        self.assertEqual(self.url, f'/messages/{self.message.id}/')

    def test_get_message_detail(self):
        """Ensure the page loads correctly and the correct template is used."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'message_detail.html')
        self.assertContains(response, self.message.subject)
        self.assertContains(response, self.message.sender.username)
        self.assertContains(response, self.message.recipient.username)
        self.assertContains(response, self.message.content)

    def test_get_message_detail_redirects_when_not_logged_in(self):
        """Ensure a user that has not logged in is redirected to login."""
        response = self.client.get(self.url)
        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={self.url}')

    def test_get_message_detail_logged_in(self):
        """Ensure a user that has logged in can view the page."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.message.subject)
        self.assertContains(response, self.message.sender.username)
        self.assertContains(response, self.message.recipient.username)

    def test_view_previous_message(self):
        """Ensure the 'View Previous Message' button works correctly."""
        previous_message = Message.objects.create(
            sender=self.user,
            recipient=self.recipient,
            subject='Previous Message',
            content='Content of the previous message.'
        )
        self.message.previous_message = previous_message
        self.message.save()
        response = self.client.get(self.url)
        previous_message_url = reverse('message_detail', kwargs={'pk': previous_message.id})
        self.assertContains(response, f'href="{previous_message_url}"')

    def test_view_next_message(self):
        """Ensure the 'View Reply' button works correctly."""
        next_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.user,
            subject='Next Message',
            content='Content of the next message.'
        )
        self.message.reply = next_message
        self.message.save()
        response = self.client.get(self.url)
        next_message_url = reverse('message_detail', kwargs={'pk': next_message.id})
        self.assertContains(response, f'href="{next_message_url}"')

    def test_reply_button(self):
        """Ensure the reply button directs the user to the correct reply URL."""
        reply_url = reverse('message_reply', kwargs={'pk': self.message.id})
        response = self.client.get(self.url)
        self.assertContains(response, f'href="{reply_url}"')
