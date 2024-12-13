from django.test import TestCase
from django.contrib.auth import get_user_model
from tutorials.forms import MessageForm
from tutorials.models import Message

User = get_user_model()

class MessageFormTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username="@sender", email="sender@example.com", password="password123")
        self.recipient = User.objects.create_user(username="@recipient", email="recipient@example.com", password="password123")

    def test_form_valid_data(self):
        """Test the form with valid data."""
        form_data = {
            "recipient": self.recipient.username,
            "subject": "Test Subject",
            "content": "This is a test message."
        }
        form = MessageForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_empty_recipient(self):
        """Test that the form raises an error for an empty recipient."""
        form_data = {
            "recipient": "",
            "subject": "Test Subject",
            "content": "This is a test message."
        }
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("recipient", form.errors)
        self.assertEqual(form.errors["recipient"], ["This field is required."])

    def test_form_invalid_recipient(self):
        """Test that the form raises an error for a non-existent recipient."""
        form_data = {
            "recipient": "@nonexistent",
            "subject": "Test Subject",
            "content": "This is a test message."
        }
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("recipient", form.errors)
        self.assertEqual(form.errors["recipient"], ["No user found with that username. Please try again."])

    def test_form_empty_subject(self):
        """Test that the form allows an empty subject."""
        form_data = {
            "recipient": self.recipient.username,
            "subject": "",
            "content": "This is a test message."
        }
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_empty_content(self):
        """Test that the form raises an error for empty content."""
        form_data = {
            "recipient": self.recipient.username,
            "subject": "Test Subject",
            "content": ""
        }
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)
        self.assertEqual(form.errors["content"], ["This field is required."])

    def test_previous_message_placeholder(self):
        """Test that the placeholder is updated for the recipient field when a previous message is passed."""
        previous_message = Message.objects.create(
            sender=self.sender, recipient=self.recipient, subject="Previous", content="Previous message."
        )
        form = MessageForm(previous_message=previous_message)
        self.assertEqual(form.fields["recipient"].widget.attrs["placeholder"], self.sender.username)

    def test_save_method_with_valid_data(self):
        """Test that the form save method works with valid data."""
        form_data = {
            "recipient": self.recipient.username,
            "subject": "Test Subject",
            "content": "This is a test message."
        }
        form = MessageForm(data=form_data)
        self.assertTrue(form.is_valid())
        message = form.save(commit=False)
        message.sender = self.sender
        message.save()

        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(message.recipient, self.recipient)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.subject, "Test Subject")
        self.assertEqual(message.content, "This is a test message.")

    def test_save_method_with_previous_message(self):
        """Test the save method with a previous message."""
        previous_message = Message.objects.create(
            sender=self.sender, recipient=self.recipient, subject="Previous", content="Previous message."
        )

        form_data = {
            "recipient": self.recipient.username,
            "subject": "Reply Subject",
            "content": "This is a reply."
        }
        form = MessageForm(data=form_data, instance=Message(previous_message=previous_message))
        self.assertTrue(form.is_valid())
        message = form.save(commit=True)

        self.assertEqual(Message.objects.count(), 2)
        self.assertEqual(message.previous_message, previous_message)
        self.assertEqual(previous_message.reply, message)
