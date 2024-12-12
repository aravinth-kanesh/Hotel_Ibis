from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import Http404
from tutorials.models import Message

class MessageDetailViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']  
    def setUp(self):
        self.sender = get_user_model().objects.get(pk=3)  
        self.recipient = get_user_model().objects.create_user(
            username="recipient",
            password="recipientpassword",
            email="recipient@example.com"
        )

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

        self.client = Client()
        self.client.login(username=self.sender.username, password="Password123")


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
        self.assertEqual(response.status_code, 403)  

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
    
    def test_reply_button(self):
        """Ensure the reply button directs the user to the correct reply URL."""
        reply_url = reverse('message_reply', kwargs={'pk': self.message.id})
        response = self.client.get(self.url)
        self.assertContains(response, f'href="{reply_url}"')
        
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