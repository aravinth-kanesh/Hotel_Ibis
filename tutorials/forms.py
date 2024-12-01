"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest, Tutor, Language, TutorLangRequest, TutorAvailability

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

        super().save(commit=False)
        
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
            
            conflicting_availability = TutorAvailability.objects.filter(
                tutor=tutor,
                day=day,
            ).exclude(id=self.instance.id)  # Exclude the current instance for updates

            for availability in conflicting_availability:
                if (
                    start_time < availability.end_time and
                    end_time > availability.start_time
                ):
                    raise forms.ValidationError("There is already an overlapping availability request for this time slot.")

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