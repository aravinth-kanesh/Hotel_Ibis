"""Forms for the tutorials app."""
from datetime import datetime, timedelta
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest, Student, Tutor, Lesson, Language, Message, TutorAvailability

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
        fields = ['first_name', 'last_name', 'username', 'email']


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
    
        if hasattr(user, 'role'):
            user.role = role

        if commit:
            user.save()
        return user
    

class StudentRequestForm(forms.ModelForm):
    is_allocated = False
    class Meta:
        model = StudentRequest

        fields = [
            'language', 'description','date', 'time', 'venue',
            'duration', 'frequency', 'term'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Enter any other requirements here.'}),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'YYYY-MM-DD',
                'class': 'form-control',
            }),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'venue': forms.TextInput(attrs={'placeholder': 'Enter venue address'}),
            'duration': forms.NumberInput(attrs={
                'placeholder': 'Enter number of minutes',
                'class': 'form-control',
            }),
            'frequency': forms.Select(),
            'term': forms.Select(),
        }
        def clean(self):
            cleaned_data = super().clean()
            language = cleaned_data.get("language")
            description = cleaned_data.get("description")
            duration = cleaned_data.get("duration")

            if duration is not None and duration <= 0:
                self.add_error("duration", "Invalid duration.")

            if not language:
                self.add_error("language", "This field is required.")

            if not description:
                self.add_error("description", "This field is required.")
            required_fields = ['date', 'time', 'venue', 'duration', 'frequency', 'term']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "This field is required.")  
                return cleaned_data

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
        username_input = self.cleaned_data['recipient'].strip()
        if not username_input:
            raise forms.ValidationError("This field is required.")

        try:
            recipient_user = User.objects.get(username__iexact=username_input)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with that username. Please try again.")

        return recipient_user
    def save(self, commit=True):
        """Overide save to handle recipient and reply """
        if not self.is_valid():
            raise ValueError("The Message could not be created because the data didn't validate.")

        message = super().save(commit=False)
    
        if 'recipient' in self.cleaned_data:
            message.recipient = self.cleaned_data["recipient"]

        if self.instance.previous_message:
            previous_message = self.instance.previous_message
            message.previous_message = previous_message

            if commit:
                message.save()
                if message.previous_message:
                    message.previous_message.reply = message
                    message.previous_message.save()

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
        required=False,
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
        
        # Extract student_request from kwargs and handle it separately
        student_request = kwargs.pop('student_request', None)
        super().__init__(*args, **kwargs)

        if student_request:
            requested_language = student_request.language  # Get the language of the student request
            
            # Filter tutors based on the requested language
            self.fields['tutor'].queryset = Tutor.objects.filter(languages=requested_language)

    def clean(self):
        """Custom validation logic."""

        cleaned_data = super().clean()

        # Call the individual validation checks
        self._validate_status_and_details(cleaned_data)
        self._validate_accepted_request(cleaned_data)

        return cleaned_data

    def _validate_status_and_details(self, cleaned_data):
        """Ensure details are provided if the status is 'denied'."""
        
        status = cleaned_data.get('status')
        details = cleaned_data.get('details')

        if status == 'denied' and not details:
            raise forms.ValidationError({
                'details': 'You must provide a reason in the Details field when denying a request.'
            })

    def _validate_accepted_request(self, cleaned_data):
        """Ensure tutor and lesson details are provided if status is 'accepted'."""
        
        status = cleaned_data.get('status')
        tutor = cleaned_data.get('tutor')
        first_lesson_date = cleaned_data.get('first_lesson_date')
        first_lesson_time = cleaned_data.get('first_lesson_time')

        if status == 'accepted':
            if not tutor:
                raise forms.ValidationError({
                    'tutor': 'You must select a tutor for accepted requests.'
                })
            if not first_lesson_date:
                raise forms.ValidationError({
                    'first_lesson_date': 'You must provide the first lesson date.'
                })
            if not first_lesson_time:
                raise forms.ValidationError({
                    'first_lesson_time': 'You must provide the first lesson time.'
                })


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
        widget=forms.SelectDateWidget()
    )
    new_time = forms.TimeField(
        label="New Time",
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    class Meta:
        model = Lesson
        fields = ['cancel_lesson', 'new_date', 'new_time']

    def __init__(self, *args, **kwargs):
        """Initialise the form and pre-fill date and time."""

        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.instance = instance

            # Pre-fill fields with original lesson data
            self.fields['new_date'].initial = instance.date
            self.fields['new_time'].initial = instance.time

    def clean(self):
        """
        Custom validation to check if either cancel_lesson is selected or new_date & new_time are provided.
        Check for scheduling conflicts for the new proposed lesson
        """
        cleaned_data = super().clean()

        cancel_lesson = cleaned_data.get('cancel_lesson')
        new_date = cleaned_data.get('new_date')
        new_time = cleaned_data.get('new_time')

        # Skip validation if the lesson is being cancelled
        if cancel_lesson:
            return cleaned_data

        # Ensure new_date and/or new_time are provided if not cancelling
        if not new_date or not new_time or (new_date == self.instance.date and new_time == self.instance.time):
            raise forms.ValidationError("New date and/or new time are required when cancelling is not selected.")

        # Convert new date and time to datetime objects
        new_start_datetime = datetime.combine(new_date, new_time)
        new_end_datetime = new_start_datetime + timedelta(minutes=self.instance.duration)  
        new_end_time = new_end_datetime.time()
        
        # Check if the tutor is available at the new time
        if not self._is_tutor_available(new_date, new_time, new_end_time):
            raise forms.ValidationError("The tutor is not available at the new proposed time.")

        # Check for conflicts with both student and tutor schedules
        if self._has_conflict(new_start_datetime, new_end_datetime):
            raise forms.ValidationError("The new date and time conflict with existing schedules.")

        return cleaned_data

    def _is_tutor_available(self, new_date, new_time, new_end_time):
        """Check if the tutor is available for the new proposed date/time."""
  
        tutor_availability = TutorAvailability.objects.filter(
            tutor=self.instance.tutor,
            day=new_date,  
            start_time__lte=new_time,  # Tutor should be available at or before the start of the new lesson
            end_time__gte=new_end_time  # Tutor should be available for the full duration
        )

        return tutor_availability.exists()

    def _has_conflict(self, new_start_datetime, new_end_datetime):
        """Check for conflicts with student and tutor schedules."""

        # Check for student conflicts
        student_conflict = self._get_conflicting_lessons(
            Lesson.objects.filter(student=self.instance.student)
            .exclude(id=self.instance.id)
            .filter(date=new_start_datetime.date()),
            new_start_datetime,
            new_end_datetime,
            "The student already has a lesson scheduled that conflicts with the new date and time."
        )

        # Check for tutor conflicts
        tutor_conflict = self._get_conflicting_lessons(
            Lesson.objects.filter(tutor=self.instance.tutor)
            .exclude(id=self.instance.id)
            .filter(date=new_start_datetime.date()),
            new_start_datetime,
            new_end_datetime,
            "The tutor already has a lesson scheduled that conflicts with the new date and time."
        )

        if student_conflict or tutor_conflict:
            return True

        return False

    def _get_conflicting_lessons(self, lessons, new_start_datetime, new_end_datetime, error_message):
        """Generic logic to check conflicts for overlapping lessons. Used for both student and tutor conflicts."""
    
        for existing_lesson in lessons:
            existing_start_datetime = datetime.combine(existing_lesson.date, existing_lesson.time)
            existing_end_datetime = existing_start_datetime + timedelta(minutes=existing_lesson.duration)

            if new_end_datetime <= existing_start_datetime or new_start_datetime >= existing_end_datetime:
                continue

            if (
                (new_start_datetime < existing_start_datetime and new_end_datetime > existing_start_datetime and new_end_datetime <= existing_end_datetime) or
                (new_start_datetime < existing_start_datetime and new_end_datetime > existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime > existing_end_datetime) or
                (new_start_datetime >= existing_start_datetime and new_end_datetime <= existing_end_datetime)          
            ):
                return True

        return False
    

class TutorAvailabilityForm(forms.ModelForm):
    REPEAT_CHOICES = [
        ('once', 'Once'),
        ('weekly', 'Repeat Weekly'),
        ('biweekly', 'Repeat Biweekly'),
    ]

    repeat = forms.ChoiceField(
        choices=REPEAT_CHOICES,
        required=True,
        error_messages={'required': 'Please select a repeat option.'},
        initial='once',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    class Meta:
        model = TutorAvailability
        fields = ['tutor', 'start_time', 'end_time', 'day', 'availability_status']
        widgets = {
            'tutor': forms.HiddenInput(),
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'availability_status': forms.Select(attrs={'class': 'form-control'}),
            'tutor': forms.Select(attrs={'class': 'form-control'}),
        
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  
        super().__init__(*args, **kwargs)
        
        if user:
            try:
                tutor = Tutor.objects.get(UserID=user)
                self.fields['tutor'].queryset = Tutor.objects.filter(id=tutor.id)
                self.fields['tutor'].initial = tutor 
            except Tutor.DoesNotExist:
                self.fields['tutor'].queryset = Tutor.objects.none()
        
        self.fields['tutor'].disabled = True
        
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day = cleaned_data.get('day')
        availability_status = cleaned_data.get('availability_status')
        tutor =  cleaned_data.get('tutor') or self.initial.get('tutor')

        if not isinstance(tutor, Tutor):
            raise forms.ValidationError("A valid Tutor instance is required.")

        
        if day and start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be earlier than end time.")

            if TutorAvailability.objects.filter(tutor=tutor, start_time=start_time, end_time=end_time, day=day, availability_status=availability_status).exists():
                raise forms.ValidationError("This time slot is already recorded.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
    
        
        if not instance.tutor:
            instance.tutor = self.initial.get('tutor')
            if not instance.tutor:
                raise ValueError("A tutor instance is required to save this form.")

        repeat_option = self.cleaned_data['repeat']
    
        if repeat_option in ['weekly', 'biweekly']:
            from tutorials.term_dates import TERM_DATES, get_term

            interval = 7 if repeat_option == 'weekly' else 14
            date = self.cleaned_data.get('day')
            term_dates = get_term(date)
            start_date = term_dates['start_date']
            end_date = term_dates['end_date']
            current_date = instance.day
            
            if not start_date <= current_date <= end_date:
                raise ValueError(f"Not in term time.")
            
            
            current_date += timedelta(days=interval)
            while current_date <= end_date:
                if not TutorAvailability.objects.filter(
                    tutor=instance.tutor,
                    day=current_date,
                    start_time=instance.start_time,
                    end_time=instance.end_time
                ).exists():
                    TutorAvailability.objects.create(
                        tutor=instance.tutor,
                        day=current_date,
                        start_time=instance.start_time,
                        end_time=instance.end_time,
                        availability_status=instance.availability_status,
                    )
                current_date += timedelta(days=interval)
        else:
            if commit:
                instance.save()
        return instance

class TutorLanguageForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Type to search or create a new language'}),
    )
    existing_language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        required=False,
        empty_label="Select an existing language",
    )

    def __init__(self, *args, **kwargs):
        initial_query = kwargs.pop('initial_query', None)
        super().__init__(*args, **kwargs)
        # Dynamically filter the queryset based on the input query
        if initial_query:
           
            self.fields['existing_language'].queryset = Language.objects.filter(name__icontains=initial_query.lower())
        else:
            self.fields['existing_language'].queryset = Language.objects.all()

    def save_or_create_language(self):
        """Handle saving the selected or creating a new language."""
        query = self.cleaned_data.get('query').strip()
        existing_language = self.cleaned_data.get('existing_language')

        if existing_language:
            return existing_language
        elif query:  # If no existing language is selected, create a new one
            language, created = Language.objects.get_or_create(name=query)
            return language
        return None
    
class RemoveLanguageForm(forms.Form):
    language_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)

    def clean_language_id(self):
        language_id = self.cleaned_data.get('language_id')
        try:
            language = Language.objects.get(id=language_id)
        except Language.DoesNotExist:
            raise forms.ValidationError("The selected language does not exist.")

        if self.tutor and language not in self.tutor.languages.all():
            raise forms.ValidationError("You do not have permission to remove this language.")
        return language

