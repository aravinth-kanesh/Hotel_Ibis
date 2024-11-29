"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest, Lesson

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

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        role = self.cleaned_data.get('role')
        if role not in ['tutor', 'student']:
            raise ValueError("Invalid role selected.")
        user.role = role
        if commit:
            user.save()
        return user

class StudentRequestForm(forms.ModelForm):
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
            'frequency': forms.Select(),
            'term': forms.Select(),
        }

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

    class Meta:
        model = Lesson 

        fields = ['status', 'details']

        widgets = {
            'status': forms.RadioSelect(),
            'details': forms.Textarea(attrs={'placeholder': 'Provide extra details.'}),
        }

    def clean(self):
        """Validate the form fields."""

        super().clean()

        # Retrieve cleaned data
        status = self.cleaned_data.get('status')
        details = self.cleaned_data.get('details')

        # Enforce details for denied lessons
        if status == 'denied' and not details:
            self.add_error('details', 'You must provide a reason in the Details field when denying a request.')

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
            # Pre-fill fields with original lesson data
            self.fields['new_date'].initial = instance.date
            self.fields['new_time'].initial = instance.time
    
    def clean(self):
        """Custom validation to check if either cancel_lesson is selected or new_date & new_time are provided."""

        cleaned_data = super().clean()
        
        cancel_lesson = cleaned_data.get('cancel_lesson')
        new_date = cleaned_data.get('new_date')
        new_time = cleaned_data.get('new_time')

        # If cancel_lesson is not selected, new_date and new_time must be filled out
        if not cancel_lesson:
            if not new_date or not new_time:
                raise forms.ValidationError("Both New Date and New Time are required when cancelling is not selected.")

        return cleaned_data