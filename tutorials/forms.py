"""Forms for the tutorials app."""
from datetime import datetime, timedelta
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest, Student, Tutor, Lesson, Language, Message, Tutor, Language, TutorLangRequest, TutorAvailability

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user
    

class UserForm(forms.ModelForm):
    """Form to update user profiles."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role']


class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user
    

class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    role = forms.ChoiceField(
        choices=[('tutor', 'Tutor'), ('student', 'Student')], 
        label="Role")
    
    language_choices = [(lang.name, lang.name) for lang in Language.objects.all()]
    languages = forms.ChoiceField(
        
        choices=language_choices,
        label = "Language"
    )

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role']

    def save(self, commit=True):
        """Create a new user."""
        role = self.cleaned_data.get('role')
        if role not in ['tutor', 'student']:
            raise ValueError("Invalid role selected.")

        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        role = self.cleaned_data.get('role')
        language = self.cleaned_data.get('languages')
        if role not in ['tutor', 'student']:
            raise ValueError("Invalid role selected.")
        user.role = role

        if commit:
            user.save()

        if user.role == 'tutor':
            if not language:
                raise forms.ValidationError("Tutors must select at least one language.")

            try:
                # Ensure the language exists in the database
                language = Language.objects.get(name=language)
            except Language.DoesNotExist:
                raise forms.ValidationError(f"Language '{language}' does not exist.")

            # Create Tutor instance and associate language
            tutor = Tutor.objects.create(UserID=user)
            tutor.languages.add(language)

            if commit:
                tutor.save()

        return user
    

class StudentRequestForm(forms.ModelForm):
    is_allocated = False
    class Meta:
        model = StudentRequest

        fields = [
            'language', 'description', 'time', 'venue',
            'duration', 'frequency', 'term'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Enter any other requirements here.'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'venue': forms.TextInput(attrs={'placeholder': 'Enter venue address'}),
            'duration': forms.NumberInput(attrs={
                'placeholder': 'Enter number of minutes',
                'class': 'form-control',
            }),
            'frequency': forms.Select(),
            'term': forms.Select(),
        }

        def clean_duration(self):
            value = self.cleaned_data['duration']
            if value is None or value <= 0:
                raise forms.ValidationError("Invalid duration.")
            return value
        

class MessageForm (forms.ModelForm):
    recipient = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '@...',
        }),
        label="Recipient",
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '....',
                'rows': 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        """Adds intended recipient into placeholder for QOl"""
        
        previous_message = kwargs.pop('previous_message', None)
        super().__init__(*args, **kwargs)

        if previous_message:
            if 'recipient' in self.fields:
                self.fields['recipient'].widget.attrs.update({
                    'placeholder': previous_message.sender.username
            })
        
    def clean_recipient(self):
        """Fuzzy matching for the recipient"""
        username_input = self.cleaned_data['recipient']

        try:
            recipient_user = User.objects.get(username__iexact=username_input)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with that username. Please try again.")

        return recipient_user
    
    def save(self, commit=True):
        """Overide save to handle recipient and reply """
        message = super().save(commit=False)
    
        message.recipient = self.cleaned_data['recipient']

        if self.instance.previous_message:
            previous_message = self.instance.previous_message
            message.previous_message = previous_message

            if commit:
                message.save()
                previous_message.reply = message
                previous_message.save()

        if commit:
            message.save()
        return message


class StudentRequestProcessingForm(forms.ModelForm):
    """Form for the admin to process student lesson requests."""

    STATUS_CHOICES = [
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]

    # Status field for admin to accept or deny the lesson request
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label='Request Status',
        widget=forms.RadioSelect
    )

    # Details field for admin to explain why the request was denied or for any necessary notes
    details = forms.CharField(
        label='Details',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Provide extra details.',
            'rows': 3,
        })
    )

    # Tutor field (using ModelChoiceField to allow selection of a tutor)
    tutor = forms.ModelChoiceField(
        queryset=Tutor.objects.all(), 
        label="Select Tutor",
        widget=forms.Select(attrs={'placeholder': 'Select a tutor'})
    )

    # Fields for first lesson date and time
    first_lesson_date = forms.DateField(
        label="First Lesson Date",
        required=False,
        widget=forms.SelectDateWidget()
    )
    first_lesson_time = forms.TimeField(
        label="First Lesson Time",
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    class Meta:
        model = Lesson
        fields = ['status', 'details', 'tutor', 'first_lesson_date', 'first_lesson_time']

    def __init__(self, *args, **kwargs):
        """Initialise the form and dynamically filter tutors."""
        
        kwargs.pop('student_request', None)  # Extract student_request from kwargs
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate the form fields."""

        super().clean()

        # Retrieve cleaned data
        status = self.cleaned_data.get('status')
        details = self.cleaned_data.get('details')
        tutor = self.cleaned_data.get('tutor')
        first_lesson_date = self.cleaned_data.get('first_lesson_date')
        first_lesson_time = self.cleaned_data.get('first_lesson_time')

        # Enforce details for denied lessons
        if status == 'denied' and not details:
            self.add_error('details', 'You must provide a reason in the Details field when denying a request.')

        # Enforce tutor, date, and time for accepted lessons
        if status == 'accepted':
            if not tutor:
                self.add_error('tutor', 'You must select a tutor for accepted requests.')
            if not first_lesson_date:
                self.add_error('first_lesson_date', 'You must provide the first lesson date.')
            if not first_lesson_time:
                self.add_error('first_lesson_time', 'You must provide the first lesson time.')

        return self.cleaned_data


class LessonUpdateForm(forms.ModelForm):
    """Form to update lesson date/time or cancel the lesson."""

    # The checkbox to cancel the lesson
    cancel_lesson = forms.BooleanField(
        label="Cancel Lesson", 
        required=False, 
        initial=False
    )
    
    # Fields for new date and time to reschedule the lesson
    new_date = forms.DateField(
        label="New Date", 
        required=False, 
        widget=forms.SelectDateWidget(attrs={'class': 'form-control'})
    )
    new_time = forms.TimeField(
        label="New Time", 
        required=False, 
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    
    class Meta:
        model = Lesson
        fields = ['cancel_lesson', 'new_date', 'new_time']

    def __init__(self, *args, **kwargs):
        """Initialize the form and pre-fill date and time."""
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            # Pre-fill fields with original lesson data
            self.fields['new_date'].initial = instance.date
            self.fields['new_time'].initial = instance.time

    def clean(self):
        """Custom validation to check if either cancel_lesson is selected or new_date & new_time are provided."""
        cleaned_data = super().clean()
        
        cancel_lesson = cleaned_data.get('cancel_lesson')
        new_date = cleaned_data.get('new_date')
        new_time = cleaned_data.get('new_time')

        # Skip validation if the lesson is being cancelled
        if cancel_lesson:
            return cleaned_data

        # Ensure new_date and/or new_time are provided if not cancelling
        if not new_date or not new_time:
            raise forms.ValidationError("New date and/or new time are required when cancelling is not selected.")

        # If the date or time has not changed, raise validation error
        if new_date == self.instance.date and new_time == self.instance.time:
            raise forms.ValidationError("You must change the date or time to update the lesson details.")

        # Convert new date and time to datetime objects
        new_start_datetime = datetime.combine(new_date, new_time)
        new_end_datetime = new_start_datetime + timedelta(minutes=self.instance.duration)  

        # Check if there are any conflicts with the student's existing lessons
        student_conflict = Lesson.objects.filter(
            student=self.instance.student
        ).exclude(id=self.instance.id).filter(
            date=new_date
        )

        # Check if there are any conflicts with the tutor's existing lessons
        tutor_conflict = Lesson.objects.filter(
            tutor=self.instance.tutor  
        ).exclude(id=self.instance.id).filter(
            date=new_date
        )

        # Check for overlap conditions with the student's timetable
        for existing_lesson in student_conflict:
            existing_start_datetime = datetime.combine(existing_lesson.date, existing_lesson.time)
            existing_end_datetime = existing_start_datetime + timedelta(minutes=existing_lesson.duration)

            # Check for overlap conditions with the student's timetable
            if (
                (new_start_datetime < existing_end_datetime and new_end_datetime > existing_start_datetime and new_end_datetime < existing_end_datetime) or
                (new_start_datetime < existing_start_datetime and new_end_datetime > existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime <= existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime > existing_end_datetime)
            ):
                raise forms.ValidationError("The student already has a lesson scheduled that conflicts with the new date and time.")

        # Check for overlap conditions with the tutor's timetable
        for existing_lesson in tutor_conflict:
            existing_start_datetime = datetime.combine(existing_lesson.date, existing_lesson.time)
            existing_end_datetime = existing_start_datetime + timedelta(minutes=existing_lesson.duration)

            # Check for overlap conditions with the tutor's timetable
            if (
                (new_start_datetime < existing_end_datetime and new_end_datetime > existing_start_datetime and new_end_datetime < existing_end_datetime) or
                (new_start_datetime < existing_start_datetime and new_end_datetime > existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime <= existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime > existing_end_datetime)
            ):
                raise forms.ValidationError("The tutor already has a lesson scheduled that conflicts with the new date and time.")

        return cleaned_data
    

class TutorLanguageRequestForm(forms.ModelForm):
    class Meta:
        model = TutorLangRequest
        fields = ['tutor', 'language', 'action', 'current_language', 'requested_language']


class TutorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TutorAvailability
        fields = ['tutor', 'start_time', 'end_time', 'day', 'availability_status']
        widgets = {
            'tutor': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'availability_status': forms.Select(attrs={'class': 'form-control'}),
        }

        def clean(self):
            cleaned_data = super().clean()
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')
            day = cleaned_data.get('day')
            tutor = self.instance.tutor  # Access the tutor instance

            if start_time and end_time and start_time >= end_time:
                raise forms.ValidationError("Start time must be earlier than end time.")
            
        # Check for overlapping availability
            if TutorAvailability.objects.filter(tutor=tutor, start_time=start_time, end_time=end_time, day=day).exists():
                raise forms.ValidationError("This time slot is already recorded.")
            return cleaned_data
        
        def save(self, commit=True):
            instance = super().save(commit=False)
            if self.initial.get('tutor'):
                instance.tutor = self.initial['tutor']
            if commit:
                instance.save()
            return instance