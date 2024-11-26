"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest

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
        label="Role"
    )

    class Meta:
        """Form options."""
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role']

    def save(self, commit=True):
        """Create a new user."""
        # Do not save the instance immediately
        user = super().save(commit=False)
        
        # Set additional attributes
        user.set_password(self.cleaned_data.get('new_password'))  # Hash the password
        user.role = self.cleaned_data.get('role')

        # Save to database only if commit=True
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


class EditUserProfileForm(forms.ModelForm):
    """Form for editing user profile details."""
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'role': forms.Select(attrs={'placeholder': 'Select a role'}),
        }

    def clean_username(self):
        """Ensure the username meets the regex validation and is unique."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        """Ensure the email is unique."""
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def save(self, commit=True):
        """Save the user profile and handle role-specific logic."""
        user = super().save(commit=False)

        # Handle role-specific group assignments
        if user.role == 'admin':
            group_name = 'Admins'
        elif user.role == 'tutor':
            group_name = 'Tutors'
        elif user.role == 'student':
            group_name = 'Students'
        else:
            group_name = None

        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.clear()  # Remove user from all groups
            user.groups.add(group)

        if commit:
            user.save()

        return user
    
