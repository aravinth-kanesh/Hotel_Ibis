from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render
from django.views import View
from django.http import JsonResponse
#
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
#
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.dateparse import parse_date
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, EditUserProfileForm
from tutorials.helpers import login_prohibited
# 
from .forms import StudentRequestForm
from .models import StudentRequest, Student, Lesson
#
from datetime import date, datetime, timedelta
import calendar
from calendar import HTMLCalendar


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
def edit_profile_view(request):
    """View to edit user profile."""
    current_user = request.user  # Get the currently logged-in user
    if request.method == "POST":
        form = EditUserProfileForm(request.POST, instance=current_user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to profile page or another relevant page
    else:
        form = EditUserProfileForm(instance=current_user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def lesson_request_view(request):
    """Handle user lesson requests."""
    if request.user.role != 'student':
        messages.error(request, "Only students can request lessons.")
        return redirect('dashboard')

    try:
        student = Student.objects.get(UserID=request.user)
    except Student.DoesNotExist:
        student = Student.objects.create(UserID=request.user)

    # Get the date from GET parameters, if available
    date_str = request.GET.get('date')
    initial_data = {}
    if date_str:
        date = parse_date(date_str)
        if date:
            initial_data['date'] = date

    if request.method == "POST":
        form = StudentRequestForm(request.POST)
        if form.is_valid():
            # Save the lesson request and associate it with the current student
            lesson_request = form.save(commit=False)
            lesson_request.student = student
            lesson_request.save()
            messages.success(request, "Your lesson request has been submitted successfully!")
            return redirect('dashboard')  # Redirect to dashboard or another appropriate page
    else:
        form = StudentRequestForm(initial=initial_data)

    return render(request, 'lesson_request.html', {'form': form})

@login_required
def calendar_view(request, year=None, month=None):
    user = request.user
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    # Get the Student instance
    try:
        student = Student.objects.get(UserID=user)
    except Student.DoesNotExist:
        # Handle the case where the student profile doesn't exist
        return redirect('dashboard')  # Or an appropriate page

    # Fetch lessons for the student
    lessons = Lesson.objects.filter(
        student=student,
        date__year=year,
        date__month=month
    )

    cal = LessonCalendar(lessons)
    html_cal = cal.formatmonth(year, month)

    # Style adjustments
    html_cal = html_cal.replace('<td ', '<td style="padding:10px; border:1px solid #ddd;" ')
    html_cal = html_cal.replace('<th ', '<th style="padding:10px; border:1px solid #ddd; background:#f5f5f5;" ')

    context = {
        'calendar': html_cal,
        'year': year,
        'month': month,
        'next_month': next_month(year, month),
        'prev_month': prev_month(year, month),
    }

    return render(request, 'calendar.html', context)

def next_month(year, month):
    if month == 12:
        return {'year': year + 1, 'month': 1}
    else:
        return {'year': year, 'month': month + 1}

def prev_month(year, month):
    if month == 1:
        return {'year': year - 1, 'month': 12}
    else:
        return {'year': year, 'month': month - 1}


@login_required
def lessons_on_day(request, year, month, day):
    user = request.user
    date_obj = date(year=int(year), month=int(month), day=int(day))

    try:
        student = Student.objects.get(UserID=user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    lessons = Lesson.objects.filter(
        student=student,
        date=date_obj
    )
    return render(request, 'lessons_on_day.html', {'lessons': lessons, 'date': date_obj})


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
        
class LessonCalendar(calendar.HTMLCalendar):
    def __init__(self, lessons):
        super().__init__()
        self.lessons = self.group_by_day(lessons)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            date_obj = date(self.year, self.month, day)
            if date.today() == date_obj:
                cssclass += ' today'

            day_html = f'<span class="date">{day}</span>'
            lesson_html = ''

            if day in self.lessons:
                lesson_list = ''
                for lesson in self.lessons[day]:
                    language_name = lesson.language.name
                    time_str = lesson.time.strftime('%H:%M')
                    # Create a link to the lesson details page (optional)
                    lesson_url = reverse('lessons_on_day', args=[self.year, self.month, day])
                    lesson_list += f'<div class="lesson-name"><a href="{lesson_url}">{time_str} - {language_name}</a></div>'
                lesson_html = f'<div class="lessons">{lesson_list}</div>'

            return self.day_cell(cssclass, day_html + lesson_html)
        else:
            return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month, withyear=True):
        self.year, self.month = year, month
        return super().formatmonth(year, month, withyear)

    def group_by_day(self, lessons):
        lessons_by_day = {}
        for lesson in lessons:
            day = lesson.date.day
            lessons_by_day.setdefault(day, []).append(lesson)
        return lessons_by_day

    def day_cell(self, cssclass, body):
        return f'<td class="{cssclass}">{body}</td>'
