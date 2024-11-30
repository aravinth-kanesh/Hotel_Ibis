from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from libgravatar import Gravatar
from django.contrib.auth.models import BaseUserManager

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
        super().save(*args, **kwargs)
    # assign groups/permissions based on role
        if self.role == 'admin':
            group, _ = Group.objects.get_or_create(name='Admins')
            self.groups.add(group)
        elif self.role == 'tutor':
            group, _ = Group.objects.get_or_create(name='Tutors')
            self.groups.add(group)
        elif self.role == 'student':
            group, _ = Group.objects.get_or_create(name='Students')
            self.groups.add(group)



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

    def __str__(self):
        return self.name
    
class Tutor(models.Model):
    """Model for tutors"""
    id = models.AutoField(primary_key=True)
    UserID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tutor_profile")
    languages = models.ManyToManyField(Language, related_name="taught_by")

    def __str__(self):
        return f"Tutor: {self.UserID.full_name}"
    
class Student(models.Model):
    """Model for student"""
    id = models.AutoField(primary_key=True)
    UserID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    paidInvoice = models.BooleanField(default=False)
    def __str__(self):
        return f"Student: {self.UserID.full_name}"

class Invoice(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="invoices")
    total_amount = models.IntegerField()
    paid = models.BooleanField(default=False)
    date_issued = models.DateField(auto_now_add=True)
    date_paid = models.DateField(null=True, blank=True)

    def __str__(self):
        status = "Paid" if self.paid else "Unpaid"
        return f"Invoice {self.id} ({status})"

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
    time = models.TimeField()
    date = models.DateField()
    venue = models.CharField(max_length=255)
    duration = models.IntegerField()  # Duration in minutes
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)

    def __str__(self):
        return f"Lesson {self.id} on {self.date} at {self.time}"

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
