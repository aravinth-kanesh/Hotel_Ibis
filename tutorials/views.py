from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.views import View
#
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
#
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tutorials.helpers import login_prohibited
# 
from .forms import StudentRequestForm
from .forms import StudentRequestProcessingForm
from .forms import LessonUpdateForm
from .models import StudentRequest, Student, Lesson, Tutor
#
from django.utils import timezone
#
from django.http import HttpResponseRedirect


@login_required
def dashboard(request):
    """Display the current user's dashboard."""

    current_user = request.user
    return render(request, 'dashboard.html', {'user': current_user})


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


@login_required
def admin_dashboard(request):
    """Display the admin's dashboard."""

    return render(request, 'admin_dashboard.html')


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
        
class StudentRequestProcessingView(LoginRequiredMixin, View):
    """View for the admin to process a student request."""

    def get(self, request, request_id):
        """Display the form to process a specific student request."""

        student_request = get_object_or_404(StudentRequest, id=request_id)
        form = StudentRequestProcessingForm(instance=student_request)

        return render(request, 'process_request.html', {'form': form, 'request': student_request})

    def post(self, request, request_id):
        """Handle form submission for processing the student request."""

        student_request = get_object_or_404(StudentRequest, id=request_id)
        form = StudentRequestProcessingForm(request.POST, instance=student_request)

        if form.is_valid():
            status = form.cleaned_data['status']
            notes = form.cleaned_data.get('details', '')  # Get rejection notes if any

            # Temporary. Will be removed when entire functionality is implemented
            self.user_tutor = get_user_model().objects.create_user(
                username='@johnny_does',
                first_name='Johnny',
                last_name='Does',
                email='johnny.does@example.com',
                password='password123',
                role='tutor'
            )
            self.tutor = Tutor.objects.create(UserID=self.user_tutor)

            # Handle the request acceptance
            if status == 'accepted':
                # Create a lesson from the student request details
                Lesson.objects.create(
                    student=student_request.student,
                    tutor=self.tutor,
                    language=student_request.language,
                    time=student_request.time,
                    date='2024-12-01',
                    venue=student_request.venue,
                    duration=student_request.duration,
                    frequency=student_request.frequency,
                    term=student_request.term
                )

                student_request.is_allocated = True
                messages.success(request, f"Request accepted! A lesson has been scheduled. {notes}")

            # Handle the request rejection
            elif status == 'denied':
                messages.warning(request, f"Request rejected. {notes}")

            # Save the student request
            student_request.save()

            return redirect('admin_dashboard')  # Redirect to the admin dashboard

        # If form is invalid, show an error message and re-render the form
        messages.error(request, "There was an error processing the request. Please try again.")

        return render(request, 'process_request.html', {'form': form, 'request': student_request})
    
class LessonUpdateView(LoginRequiredMixin, View):
    """View for changing or cancelling a lesson."""

    def get(self, request, lesson_id):
        """Display the form for changing or cancelling a lesson."""
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        form = LessonUpdateForm()

        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})

    def post(self, request, lesson_id):
        """Handle the form submission for changing or cancelling a lesson."""

        lesson = get_object_or_404(Lesson, id=lesson_id)
        form = LessonUpdateForm(request.POST)

        if form.is_valid():
            cancel_lesson = form.cleaned_data.get('cancel_lesson')

            if cancel_lesson:
                # If the lesson is cancelled, delete it and redirect
                lesson.delete()
                
                messages.success(request, "Lesson successfully cancelled.")

                return redirect('admin_dashboard')  # Redirect to the admin dashboard

            # Update lesson fields explicitly instead of using `instance`
            lesson.date = form.cleaned_data['new_date']
            lesson.time = form.cleaned_data['new_time']
            lesson.save()
            
            messages.success(request, "Lesson details successfully updated.")

            return redirect('admin_dashboard') 

        # If the form is invalid, re-render with errors
        messages.error(request, "There was an error updating the lesson. Please try again.")

        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})