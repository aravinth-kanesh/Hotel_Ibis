from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.forms import ValidationError
from libgravatar import Gravatar
from django.contrib.auth.models import BaseUserManager
from datetime import time  
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    ROLE_CHOICES = [
        ('tutor', 'Tutor'),
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    # adding according to database schema i made
    
    id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=10, choices= ROLE_CHOICES, default='student')
    def save(self, *args, **kwargs):
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValueError(f"Invalid role: {self.role}. Choose from: {[choice[0] for choice in self.ROLE_CHOICES]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)


# model for lang, tutor, student, invoice, class

class Language(models.Model):
    """ languages supported by tutors"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        # Normalize the name to lowercase before saving
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name.title()
    
class Tutor(models.Model):
    """Model for tutors"""
    id = models.AutoField(primary_key=True)
    UserID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tutor_profile")
    languages = models.ManyToManyField(Language, related_name="taught_by")
    
    
    def __str__(self):
        languages = ", ".join([language.name for language in self.languages.all()])
        print(languages)
        return f"{self.UserID.first_name} {self.UserID.last_name} - {languages if languages else 'No languages assigned'}"
    
class Student(models.Model):
    """Model for student"""
    id = models.AutoField(primary_key=True)
    UserID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    def __str__(self):
        return f"Student: {self.UserID.username}"

#All students have regular sessions 
# (every week/fortnight, same time, same venue, same tutor)
# The lessons taken in one term normally continue in the next term, 
# with the same tutor, frequency, lesson duration, time, and venue, 
# unless the student or tutor requests a change or cancellation of the lessons.
class Lesson(models.Model):
    FREQUENCY_CHOICES = [
        ('once a week', 'Once a week'),
        ('once per fortnight', 'Once per fortnight'),
    ]
    TERM_CHOICES = [
        ('sept-christmas', 'September-Christmas'),
        ('jan-easter', 'January-Easter'),
        ('may-july', 'May-July'),
    ]

    id = models.AutoField(primary_key=True)
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="classes")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="classes")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="classes")
    time = models.TimeField(default=time(9, 0))
    date = models.DateField(default=timezone.now())
    venue = models.CharField(max_length=255, default="TBD")
    duration = models.IntegerField(default=60)  # Duration in minutes
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once a week')
    term = models.CharField(max_length=20, choices=TERM_CHOICES, default='sept-christmas')
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now=True)

    def get_price(self):
        return self.price
    
    def get_occurrence_dates(self):
        from .term_dates import TERM_DATES

        term_dates = TERM_DATES.get(self.term)
        if not term_dates:
            return []

        start_date = max(self.date, term_dates['start_date'])  # Ensure the lesson doesn't start before the term
        end_date = term_dates['end_date']

        occurrence_dates = []
        current_date = start_date

        # Determine the interval between lessons
        if self.frequency == 'once a week':
            delta = timedelta(weeks=1)
        elif self.frequency == 'once per fortnight':
            delta = timedelta(weeks=2)
        else:
            return []

        # Generate dates until the end of the term
        while current_date <= end_date:
            occurrence_dates.append(current_date)
            current_date += delta

        return occurrence_dates

    def calculate_lesson_total(self):
        # Calculate the total cost of this lesson over the term
        price_per_lesson = self.get_price()
        if self.frequency == 'once a week':
            num_lessons = 13  # 13 weeks in a term
        elif self.frequency == 'once per fortnight':
            num_lessons = 7   # Approximately 7 lessons in a term
        else:
            num_lessons = 0   # Default to 0 if frequency is unknown
        return price_per_lesson * num_lessons

    def __str__(self):
        return f"Lesson {self.id} ({self.language.name}) with {self.student.UserID.username} on {self.date} at {self.time}"


# for handling student reqs
class StudentRequest(models.Model):
    FREQUENCY_CHOICES = [
        ('once a week', 'Once a week'),
        ('once per fortnight', 'Once per fortnight'),
    ]
    TERM_CHOICES = [
        ('sept-christmas', 'September-Christmas'),
        ('jan-easter', 'January-Easter'),
        ('may-july', 'May-July'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name ="classrequest")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name = "classrequest" )
    description = models.TextField()
    is_allocated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    time = models.TimeField()
    venue = models.TextField()
    duration = models.IntegerField() 
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    def __str__(self):
        return f"Request {self.id} by {self.student.UserID.username} for {self.language.name}"
    
class Message (models.Model):
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,  related_name="received_messages", db_index=True)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,  related_name="sent_messages", db_index=True)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    #if object is reply
    previous_message = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )
    #replies to the object
    reply = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name="replied_by"
    )
    class Meta:
        ordering = ["-created_at"]
        indexes = [
        models.Index(fields=["sender", "created_at"]),  
        models.Index(fields=["recipient"]),            
        models.Index(fields=["created_at"]),          
    ]

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} - {self.subject[:30]}"
    
class Invoice(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="invoices")
    lessons = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="invoices", default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    date_issued = models.DateField(auto_now_add=True)
    date_paid = models.DateField(null=True, blank=True)

    def calculate_total_amount(self):
        total = 0
        for lesson in self.lessons.all():
            lesson_total = lesson.calculate_lesson_total()
            total += lesson_total
        self.total_amount = total
        self.save()

    def __str__(self):
        status = "Paid" if self.paid else "Unpaid"
        return f"Invoice {self.id} ({status})"
    

class TutorAvailability(models.Model):
    CHOICE = [
        ('available', 'Available'),
        ('not_available', 'Not Available'),
    ]
    ACTION = [
        ('edit', 'Edit'),
        ('delete', 'Delete')
    ]
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="availability")
    start_time = models.TimeField(default="09:00")
    end_time = models.TimeField()
    day = models.DateField()
    availability_status = models.CharField(max_length=20, choices=CHOICE, default='available')
    action = models.CharField(max_length=10, choices=ACTION, default='edit')

    def __str__(self):
        return f"{self.tutor.UserID.full_name} - {self.day} - from {self.start_time} to {self.end_time} - ({self.availability_status})"
    
    def clean(self):
        """Ensure start_time is before end_time."""
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")