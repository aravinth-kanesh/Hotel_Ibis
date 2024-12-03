from itertools import count
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import QuerySet
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
#
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
#
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from pytz import timezone
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tutorials.helpers import login_prohibited
# 
from .forms import StudentRequestForm, TutorAvailabilityForm
from .models import StudentRequest, Student, Tutor, TutorLangRequest, Language, Lesson, TutorAvailability
#
from datetime import date, datetime, timedelta
import calendar
from calendar import HTMLCalendar

@login_required
def dashboard(request):
    """Display the current user's dashboard."""
    current_user = request.user
    user_role = current_user.role
    if user_role == 'admin':
        context = {
            'user': current_user,
            'role': user_role,
        }
    elif user_role == 'student':
        context = {
            'user': current_user,
            'role': user_role
        }
    elif user_role == 'tutor':
        try:
            tutor = current_user.tutor_profile
            availabilities = TutorAvailability.objects.filter(tutor=tutor)
        except Tutor.DoesNotExist:
            return HttpResponseBadRequest("You are not authorized to view this page")

        context = {
            'user': current_user,
            'role': user_role,
            'tutor': tutor,
            'availabilities': availabilities,  # Pass availability data to the template
        }
        return render(request, 'tutor_dashboard.html', context)
    else:
        return render(request, 'dashboard.html', context)


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class StudentRequestCreateView(LoginRequiredMixin, CreateView):
    """view to display the StudentRequest form and handle submissions."""
    model = StudentRequest
    form_class = StudentRequestForm
    template_name = 'student_request_form.html'
    success_url = reverse_lazy('my_requests') 

    def form_valid(self, form):
        """attach the logged-in student to the form before saving."""
        # try:
        #     student = self.request.user.student_profile  
        # except Student.DoesNotExist:
        #     return redirect('error_page')
        form.instance.created_at = timezone.now()
        form.instance.student = student  
        return super().form_valid(form)


class StudentRequestListView(LoginRequiredMixin, ListView):
    """view to display all requests made by the logged-in student."""
    model = StudentRequest
    template_name = 'student_requests_list.html'
    context_object_name = 'requests' 

    def get_queryset(self):
        """filter the requests to show only those created by the logged-in student."""
        try:
            student = self.request.user.student_profile
            return StudentRequest.objects.filter(student=student).order_by('-created_at')
        except Student.DoesNotExist:
            return StudentRequest.objects.none() 

class TutorLangRequestView(LoginRequiredMixin, View):
    """View for tutors to manage language requests."""
    model = TutorLangRequest
    template_name = "tutor_lang_request.html"

    def get(self, request):
        """Handle GET request to display the current languages and the form."""
        try:
            tutor = request.user.tutor_profile
        except Tutor.DoesNotExist:
            return HttpResponseBadRequest("You are not authorized to manage languages.")

        context = {
            "tutor": tutor,
            "languages": tutor.languages.all(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request to manage tutor languages."""
        try:
            tutor = request.user.tutor_profile
        except Tutor.DoesNotExist:
            return HttpResponseBadRequest("You are not authorized to manage languages.")

        action = request.POST.get("action")
        language_name = request.POST.get("language")

        if action == "add":
            # Add a new language
            if language_name:
                language, created = Language.objects.get_or_create(name=language_name)
                if created:
                    print(f"Created new language: {language.name}")
                else:
                    print(f"Retrieved existing language: {language.name}")
                tutor.languages.add(language)
            TutorLangRequest.objects.create(
            tutor=tutor,
            action="add",
            requested_language=language
        )

        elif action == "delete":
            # Delete an existing language
            if language_name:
                try:
                    language = tutor.languages.get(name=language_name)
                    tutor.languages.remove(language)
                    TutorLangRequest.objects.create(
                        tutor=tutor,
                        action="remove",
                        current_language=language
                    )
                except Language.DoesNotExist:
                    pass  # Ignore if the language doesn't exist

        elif action == "change":
            # Change a language
            old_language_name = request.POST.get("old_language")
            if language_name and old_language_name:
                try:
                    old_language = tutor.languages.get(name=old_language_name)
                    tutor.languages.remove(old_language)
                    TutorLangRequest.objects.create(
                        tutor=tutor,
                        action="change",
                        current_language=old_language,
                        requested_language=new_language
                    )
                except Language.DoesNotExist:
                    pass  # Ignore if the old language doesn't exist
                new_language, _ = Language.objects.get_or_create(name=language_name)
                tutor.languages.add(new_language)

        return redirect("tutor_lang_request")  # Redirect to the same page to prevent form resubmission
    

