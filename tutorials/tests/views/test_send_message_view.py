from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Message
from tutorials.forms import MessageForm

class SendMessageViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']

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
        self.client.login(username=self.sender.username, password="Password123")

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
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {
            "recipient": "recipient",
            "subject": "Test Message",
            "content": "This is a test message.",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse("all_messages"))  
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
        self.assertEqual(response.status_code, 200)  
        self.assertIn("form", response.context) 
        form = response.context["form"]

        self.assertTrue(form.is_bound) 
        self.assertTrue(form.errors)

    
        
        self.assertIn("recipient", form.errors)
        self.assertEqual(form.errors["recipient"], ["This field is required."])
        self.assertIn("subject", form.errors)
        self.assertEqual(form.errors["subject"], ["This field is required."])
        self.assertIn("content", form.errors)
        self.assertEqual(form.errors["content"], ["This field is required."])

    def test_reply_message_context(self):
        """Test that the reply message is passed in the context when reply_id is provided."""
        reply_message = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Original Message",
            content="This is the original message."
        )
        url_with_reply = reverse("reply_message", kwargs={"reply_id": reply_message.id})
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
        url_with_reply = reverse("reply_message", kwargs={"reply_id": original_message.id})
        data = {
            "recipient": self.sender.username,
            "subject": "Re: Original Message",
            "content": "This is a reply to the original message.",
        }
        response = self.client.post(url_with_reply, data)
        self.assertEqual(response.status_code, 302)
        reply_message = Message.objects.filter(subject="Re: Original Message").first()
        self.assertIsNotNone(reply_message, "Reply message was not created.")


        self.assertEqual(reply_message.previous_message.subject, "Original Message")
