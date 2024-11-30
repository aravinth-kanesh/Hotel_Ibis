from django.test import TestCase
from tutorials.models import Message, User

class MessageModelTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username="johndoe", email="johndoe@example.com")
        self.recipient = User.objects.create(username="janedoe", email="janedoe@example.com")

        # Create a test message
        self.message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Test Subject",
            content="This is a test message."
        )
        def test_message_string_representation(self):
            """Test the __str__ method of the Message model."""
            expected_str = f"Message from {self.sender} to {self.recipient} - Test Subject"
            self.assertEqual(str(self.message), expected_str)

        def test_message_creation(self):
            """Test that a message is correctly created."""
            self.assertEqual(self.message.sender, self.sender)
            self.assertEqual(self.message.recipient, self.recipient)
            self.assertEqual(self.message.subject, "Test Subject")
            self.assertEqual(self.message.content, "This is a test message.")
            self.assertIsNone(self.message.previous_message)
            self.assertIsNone(self.message.reply)

        def test_reply_to_message(self):
            """Test creating a reply to a message."""
            reply_message = Message.objects.create(
                sender=self.recipient,
                recipient=self.sender,
                subject="Re: Test Subject",
                content="This is a reply.",
                previous_message=self.message
            )

            # Assert the reply links to the original message
            self.assertEqual(reply_message.previous_message, self.message)
            self.assertEqual(reply_message.sender, self.recipient)
            self.assertEqual(reply_message.recipient, self.sender)

            # Assert the original message has the reply linked
            self.message.reply = reply_message
            self.message.save()
            self.assertEqual(self.message.reply, reply_message)

        def test_message_querying(self):
            """Test querying sent and received messages."""
            # Create additional messages
            Message.objects.create(
                sender=self.sender,
                recipient=self.recipient,
                subject="Another Test",
                content="Another test message."
            )
            Message.objects.create(
                sender=self.recipient,
                recipient=self.sender,
                subject="Reply to Another Test",
                content="Reply to another test message."
            )

            # Check sent messages
            sent_messages = Message.objects.filter(sender=self.sender)
            self.assertEqual(sent_messages.count(), 2)

            # Check received messages
            received_messages = Message.objects.filter(recipient=self.recipient)
            self.assertEqual(received_messages.count(), 2)

        def test_delete_user_and_message_behavior(self):
            """Test behavior when a sender or recipient user is deleted."""
            self.sender.delete()

            # Reload the message
            message = Message.objects.get(id=self.message.id)
            self.assertIsNone(message.sender)  # Sender should be set to NULL
            self.assertEqual(message.recipient, self.recipient)  # Recipient should remain intact
            
        def test_meta_ordering(self):
            """Test that messages are ordered by created_at in descending order."""
            earlier_message = Message.objects.create(
                sender=self.sender,
                recipient=self.recipient,
                subject="Earlier Test",
                content="This is an earlier test message."
            )
            later_message = Message.objects.create(
                sender=self.sender,
                recipient=self.recipient,
                subject="Later Test",
                content="This is a later test message."
            )

            messages = Message.objects.all()
            self.assertEqual(messages.first(), later_message)  # Later message comes first
            self.assertEqual(messages.last(), earlier_message)  # Earlier message comes last


