"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, StudentRequest , Message

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
