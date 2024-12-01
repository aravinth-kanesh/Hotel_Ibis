from datetime import date, datetime, time, timedelta
from django.db.models import Q
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
    # Define term ranges and frequency-to-days mapping as class attributes

    """Commit test"""

    TERM_RANGES = {
        'sept-christmas': (date(2024, 9, 1), date(2024, 12, 25)),
        'jan-easter': (date(2025, 1, 1), date(2025, 4, 12)),
        'may-july': (date(2025, 5, 1), date(2025, 7, 31)),
    }

    FREQUENCY_TO_DAYS = {
        'once a week': 7,
        'once per fortnight': 14,
    }

    def get(self, request, request_id):
        student_request = get_object_or_404(StudentRequest, id=request_id)

        form = StudentRequestProcessingForm(student_request=student_request)

        return render(request, 'process_request.html', {'form': form, 'request': student_request})

    def post(self, request, request_id):
        student_request = get_object_or_404(StudentRequest, id=request_id)

        form = StudentRequestProcessingForm(request.POST, student_request=student_request)

        if form.is_valid():
            status = form.cleaned_data['status']
            details = form.cleaned_data.get('details', '')
            tutor = form.cleaned_data['tutor']
            first_lesson_date = form.cleaned_data['first_lesson_date']
            first_lesson_time = form.cleaned_data['first_lesson_time']

            if status == 'accepted':
                first_lesson_datetime = datetime.combine(first_lesson_date, first_lesson_time)
                frequency = student_request.frequency
                term = student_request.term
                duration = student_request.duration
                venue = student_request.venue

                term_start, term_end = self.TERM_RANGES.get(term, (None, None))

                # Schedule lessons for the term
                scheduled_lessons = self.schedule_lessons_for_term(
                    tutor, student_request.student, student_request.language,
                    first_lesson_datetime, frequency, duration, term_start, term_end, venue
                )

                if scheduled_lessons:
                    messages.success(request, f"Request accepted! {len(scheduled_lessons)} lessons have been scheduled.")
                    student_request.is_allocated = True
                else:
                    messages.error(request, "Unable to schedule lessons due to conflicts.")
            else:
                student_request.is_allocated = False
                messages.warning(request, f"Request rejected. {details}")

            student_request.save()

            return redirect('admin_dashboard')

        messages.error(request, "There was an error processing the request. Please try again.")

        return render(request, 'process_request.html', {'form': form, 'request': student_request})

    def schedule_lessons_for_term(self, tutor, student, language, start_datetime, frequency, duration, term_start, term_end, venue):
        """Schedules lessons for the requested term, resolving conflicts dynamically."""

        scheduled_lessons = []
        current_datetime = start_datetime
        days_between_lessons = self.FREQUENCY_TO_DAYS.get(frequency, 7)

        while current_datetime.date() <= term_end:
            if current_datetime.date() >= term_start:
                available_slot = self.find_available_slot(tutor, student, current_datetime.date(), current_datetime.time(), duration)
                if available_slot:
                    lesson = Lesson.objects.create(
                        student=student,
                        tutor=tutor,
                        language=language,
                        date=available_slot.date(),
                        time=available_slot.time(),
                        duration=duration,
                        venue=venue
                    )
                    scheduled_lessons.append(lesson)
                else:
                    break  

            current_datetime += timedelta(days=days_between_lessons)

        return scheduled_lessons

    def find_available_slot(self, tutor, student, proposed_date, proposed_time, duration, max_days_to_search=7):
        """Finds an available slot for a lesson, resolving conflicts dynamically."""
        
        day_delta = timedelta(minutes=30)  # Interval to check for free slots
        max_time = time(21, 0)  # End of the available time range (9 PM)

        def get_earliest_start_time(date):
            if date.weekday() < 5:
                return time(15, 0)  # 3 PM weekdays
            else:
                return time(10, 0)  # 10 AM weekends

        for day_offset in range(max_days_to_search):
            check_date = proposed_date + timedelta(days=day_offset)
            earliest_start = get_earliest_start_time(check_date)

            # Generate time slots before and after the proposed time
            slots_before = self.generate_time_slots(check_date, earliest_start, proposed_time, day_delta, duration)
            slots_after = self.generate_time_slots(check_date, proposed_time, max_time, day_delta, duration)

            for slots in (slots_before, slots_after):
                for check_start_datetime in slots:
                    # Calculate the end time of the new proposed lesson
                    check_end_datetime = check_start_datetime + timedelta(minutes=duration)
                    check_end_time = check_end_datetime.time()

                    # Check for conflicts with student lessons
                    student_conflict = False
                    student_conflict_found = False
                    student_conflict = Lesson.objects.filter(
                        student=student,
                        date=check_start_datetime.date()  # Same date as the new lesson
                    )

                    # Iterate over the existing lessons for the student
                    for existing_lesson in student_conflict:
                        # Calculate the end time of the existing lesson
                        existing_end_time = (datetime.combine(existing_lesson.date, existing_lesson.time) + timedelta(minutes=existing_lesson.duration)).time()

                        # Check for the four types of conflicts
                        if (
                            (check_start_datetime.time() < existing_end_time and check_end_time > existing_lesson.time) or  # 1. New lesson starts before, ends after
                            (check_start_datetime.time() < existing_lesson.time and check_end_time > existing_lesson.time and check_end_time <= existing_end_time) or  # 2. New lesson starts before and ends during
                            (check_start_datetime.time() >= existing_lesson.time and check_start_datetime.time() < existing_end_time and check_end_time <= existing_end_time) or  # 3. New lesson starts during and ends during
                            (check_start_datetime.time() >= existing_lesson.time and check_start_datetime.time() < existing_end_time and check_end_time > existing_end_time)  # 4. New lesson starts during and ends after
                        ):
                            student_conflict_found = True
                            break

                    # Check for conflicts with tutor lessons
                    tutor_conflict = False
                    tutor_conflict_found = False
                    tutor_conflict = Lesson.objects.filter(
                        tutor=tutor,
                        date=check_start_datetime.date()  # Same date as the new lesson
                    )

                    # Iterate over the existing lessons for the tutor
                    for existing_lesson in tutor_conflict:
                        # Calculate the end time of the existing lesson
                        existing_end_time = (datetime.combine(existing_lesson.date, existing_lesson.time) + timedelta(minutes=existing_lesson.duration)).time()

                        # Check for the four types of conflicts
                        if (
                            (check_start_datetime.time() < existing_end_time and check_end_time > existing_lesson.time) or  # 1. New lesson starts before, ends after
                            (check_start_datetime.time() < existing_lesson.time and check_end_time > existing_lesson.time and check_end_time <= existing_end_time) or  # 2. New lesson starts before and ends during
                            (check_start_datetime.time() >= existing_lesson.time and check_start_datetime.time() < existing_end_time and check_end_time <= existing_end_time) or  # 3. New lesson starts during and ends during
                            (check_start_datetime.time() >= existing_lesson.time and check_start_datetime.time() < existing_end_time and check_end_time > existing_end_time)  # 4. New lesson starts during and ends after
                        ):
                            tutor_conflict_found = True
                            break

                    # If conflicts are found for both the student and tutor, skip this slot and continue
                    if student_conflict_found or tutor_conflict_found:
                        continue  # Skip to the next available slot

                    # If no conflicts, return the available slot
                    return check_start_datetime 

        return None

    def generate_time_slots(self, date, start_time, end_time, interval, duration):
        """Generate time slots for a given date within a specified start and end range."""

        slots = []
        current_time = datetime.combine(date, start_time)

        while current_time.time() < end_time:
            slots.append(current_time)
            current_time += interval

        return slots
    
class LessonUpdateView(LoginRequiredMixin, View):
    """View for changing or cancelling a lesson."""

    def get(self, request, lesson_id):
        """Display the form for changing or cancelling a lesson."""
        
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Pass the lesson instance to the form (change 'lesson_instance' to 'instance')
        form = LessonUpdateForm(instance=lesson)

        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})

    def post(self, request, lesson_id):
        """Handle the form submission for changing or cancelling a lesson."""

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Pass the lesson instance to the form (change 'lesson_instance' to 'instance')
        form = LessonUpdateForm(request.POST, instance=lesson)

        if form.is_valid():
            cancel_lesson = form.cleaned_data.get('cancel_lesson')

            if cancel_lesson:
                # If the lesson is cancelled, delete it and redirect
                lesson.delete()

                messages.success(request, "Lesson successfully cancelled.")

                return redirect('admin_dashboard')  # Redirect to the admin dashboard

            # Update lesson fields explicitly
            lesson.date = form.cleaned_data['new_date']
            lesson.time = form.cleaned_data['new_time']

            lesson.save()
            
            messages.success(request, "Lesson details successfully updated.")

            return redirect('admin_dashboard')

        # If the form is invalid, re-render with errors
        messages.error(request, "There was an error updating the lesson. Please try again.")

        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})