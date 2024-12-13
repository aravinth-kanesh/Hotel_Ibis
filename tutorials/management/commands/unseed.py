from django.core.management.base import BaseCommand, CommandError
from tutorials.models import User, Tutor, Student, Language, StudentRequest, TutorAvailability, Message, Invoice, Lesson

class Command(BaseCommand):
    """Build automation command to unseed the database."""
    
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        """Unseed the database."""

        Message.objects.all().delete()
        TutorAvailability.objects.all().delete()
        StudentRequest.objects.all().delete()
        Lesson.objects.all().delete()
        Invoice.objects.all().delete()  # If you have an Invoice model
        Language.objects.all().delete()

        User.objects.filter(is_staff=False).delete()