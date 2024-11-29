from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils.safestring import mark_safe

#
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
#
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.dateparse import parse_date
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tutorials.helpers import login_prohibited
from itertools import chain
# 
from .forms import StudentRequestForm
from .models import StudentRequest, Student, Lesson, Tutor, Invoice
from .utils import generate_calendar, LessonCalendar
#
from datetime import date, datetime, timedelta
import calendar
from calendar import HTMLCalendar, monthrange


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
def tutor_calendar_view(request, year=None, month=None):
    user = request.user
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    # Get the Tutor instance
    try:
        tutor = Tutor.objects.get(UserID=user)
    except Tutor.DoesNotExist:
        return redirect('dashboard')

    # Fetch lessons for the tutor
    lessons = Lesson.objects.filter(
        tutor=tutor,
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

    return render(request, 'tutor_calendar.html', context)

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


@login_required
def lessons_on_day_tutor(request, year, month, day):
    user = request.user
    date_obj = date(year=int(year), month=int(month), day=int(day))

    try:
        tutor = Tutor.objects.get(UserID=user)
    except Tutor.DoesNotExist:
        return redirect('dashboard')  # Or an appropriate page

    lessons = Lesson.objects.filter(
        tutor=tutor,
        date=date_obj
    )
    return render(request, 'lessons_on_day_tutor.html', {'lessons': lessons, 'date': date_obj})

#need to add admin required decorator later
@login_required
def student_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    # Retrieve all students along with their unpaid invoice count
    students = Student.objects.annotate(
        unpaid_invoices=Count('invoices', filter=Q(invoices__paid=False))
    )
    return render(request, 'student_list.html', {'students': students})


#need to add admin decorator here also
def create_invoice(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    # Fetch lessons not yet invoiced
    lessons = Lesson.objects.filter(student=student, invoices__isnull=True)
    tutor = None
    if lessons.exists():
        tutor = lessons.first().tutor
    else:
        messages.error(request, "No lessons to invoice for this student.")
        return redirect('student_list')

    if request.method == 'POST':
        # Create the invoice
        invoice = Invoice.objects.create(
            student=student,
            tutor=tutor,
            paid=False,
            total_amount = 0.0,
        )
        invoice.lessons.set(lessons)
        invoice.calculate_total_amount()
        messages.success(request, f"Invoice {invoice.id} created for {student.UserID.full_name()}.")
        return redirect('invoice_details', invoice_id=invoice.id)

    return render(request, 'create_invoice.html', {
        'student': student,
        'lessons': lessons,
    })


@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Access Control
    if request.user.role == 'student':
        if request.user != invoice.student.UserID:
            return redirect('dashboard')
    elif request.user.role == 'admin':
        # Admins can view any invoice
        pass
    else:
        # Other roles are not allowed
        return redirect('dashboard')

    return render(request, 'invoice_details.html', {'invoice': invoice})


@login_required
def student_invoices(request):
    user = request.user
    try:
        student = Student.objects.get(UserID=user)
    except Student.DoesNotExist:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('dashboard')

    invoices = Invoice.objects.filter(student=student)
    return render(request, 'invoice_list.html', {'invoices': invoices})


@login_required
def pay_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Ensure only the student can pay their own invoice
    if request.user != invoice.student.UserID:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('dashboard')

    if request.method == 'POST':
        invoice.paid = True
        invoice.date_paid = timezone.now()
        invoice.save()
        messages.success(request, f"Invoice {invoice.id} marked as paid.")
        return redirect('invoice_detail', invoice_id=invoice.id)

    return render(request, 'pay_invoice.html', {'invoice': invoice})


@login_required
def student_invoices_admin(request, student_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    student = get_object_or_404(Student, id=student_id)
    invoices = student.invoices.all()
    return render(request, 'student_invoices_admin.html', {
        'student': student,
        'invoices': invoices,
    })


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
                # Build the lesson list
                lesson_list = ''
                for lesson in self.lessons[day]:
                    language_name = lesson.language.name
                    time_str = lesson.time.strftime('%H:%M')
                    # Include student's name
                    student_name = lesson.student.UserID.get_full_name()
                    # Create a link to the lesson details page
                    lesson_url = reverse('lessons_on_day_tutor', args=[self.year, self.month, day])
                    # Build the lesson HTML
                    lesson_list += f'''
                        <div class="lesson-name">
                            <a href="{lesson_url}">
                                {time_str} - {language_name} with {student_name}
                            </a>
                        </div>
                    '''
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
