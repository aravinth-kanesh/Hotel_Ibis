from datetime import date, datetime, time, timedelta
from django.db.models import Q
from difflib import get_close_matches
from itertools import count
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import QuerySet
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils.safestring import mark_safe

#
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
#
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.dateparse import parse_date
from pytz import timezone
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tutorials.helpers import login_prohibited
from django.contrib.auth import get_user_model
from itertools import chain
# 
from .forms import StudentRequestForm, MessageForm, LessonUpdateForm, StudentRequestProcessingForm , TutorAvailabilityForm, TutorLanguageForm, RemoveLanguageForm
from .models import StudentRequest, Student, Message, Lesson, User, Invoice, Tutor, Lesson, Tutor, Invoice, TutorAvailability, Language
from .utils import generate_calendar, LessonCalendar
from datetime import date, datetime, timedelta
import calendar
from calendar import HTMLCalendar, monthrange
from django.utils import timezone
from decimal import Decimal



@login_required
def dashboard(request):
    """Display the current user's dashboard."""
    user = request.user
    tab = request.GET.get('tab', 'accounts')  

    context = {'user': user, 'tab': tab}

    if user.role == 'admin':

        search_query = request.GET.get('search', '')
        sort_query = request.GET.get('sort_query', '')
        action_filter = request.GET.get('action_filter', '')

        # Fetch users with optional filters
        User = get_user_model()
        users = User.objects.all()
        if search_query:
            users = users.filter(username__icontains=search_query)
        if sort_query:
            users = users.filter(role=sort_query)

        # Add unallocated requests and invoices for students
        students = Student.objects.all()
        student_data = []
        for student in students:
            unallocated_request = get_unallocated_requests(student)
            allocated_lesson = get_allocated_lesson(student)
            invoice = get_invoice_for_lesson(student)
            student_data.append({
                'student': student,
                'unallocated_request': unallocated_request,
                'allocated_lesson': allocated_lesson,
                'invoice': invoice,
            })
        if action_filter == 'unallocated':
            student_data = [
                data for data in student_data if data['unallocated_request']
            ]
        elif action_filter == 'allocated':
            student_data = [
                data for data in student_data if data['allocated_lesson']
            ]
        elif action_filter == 'no_actions':
            student_data = [
                data for data in student_data
                if not data['unallocated_request'] and not data['allocated_lesson']
            ]
        
        tutors = Tutor.objects.all()
        tutor_data = [{'tutor': tutor} for tutor in tutors]

        lessons = Lesson.objects.all()
        lessons_data = [{'lesson': lesson} for lesson in lessons]
        
        invoices = Invoice.objects.all()
        invoices_data = [{'invoice': invoice} for invoice in invoices]


        context.update({
            'users': users,
            'student_data': student_data,
            'tutor_data': tutor_data,
            'lessons_data': lessons_data,
            'invoices_data': invoices_data,
            'search_query': search_query,
            'sort_query': sort_query,
            'action_filter': action_filter,
        })

    elif user.role == 'tutor':
        availabilities = TutorAvailability.objects.filter(tutor__UserID=user)
        lessons = Lesson.objects.filter(tutor__UserID=user)
        context.update({'lessons': lessons,
                        'availabilities': availabilities,})

    elif user.role == 'student':
  
        lessons = Lesson.objects.filter(student__UserID=user)
        invoice = lessons.first().invoice
        context.update({'lessons': lessons, 'invoice': invoice})

    return render(request, 'dashboard.html', context)

@login_required
def update_user_role(request, user_id):
    if request.method == "POST" and request.user.role == 'admin':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        if new_role in dict(User.ROLE_CHOICES):
            user.role = new_role
            user.save()
            messages.success(request, f"Role updated for {user.username}.")
        return redirect('dashboard')
@login_required
def delete_user(request, user_id):
    if request.method == "POST" and request.user.role == 'admin':
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, f"User {user.username} deleted successfully.")
        return redirect('dashboard')
def get_unallocated_requests(student):
    # Ensure we are working with a Student instance
    if isinstance(student, Student):
        return StudentRequest.objects.filter(student=student, is_allocated=False).order_by('-created_at').first()
    return None

def get_allocated_lesson(student):
    if isinstance(student, Student):
        return Lesson.objects.filter(student=student).order_by('-created_at').first()
    return None

def get_invoice_for_lesson(student):
    if student:
        return Invoice.objects.filter(student=student).first()
    return None


@login_required
def approve_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST" and request.user.role in ['admin']:
        invoice.approved = True
        invoice.save()
        messages.success(request, f"Approved invoice successfully.")
    else:
        messages.success(request, f"Invoice already approved.")
    return redirect('dashboard')



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

    cal = LessonCalendar(lessons, year=2024, month=12)
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

    cal = LessonCalendar(lessons, year=2024, month=12)
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


@login_required
def student_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    # Retrieve all students along with their unpaid invoice count
    students = Student.objects.annotate(
        unpaid_invoices=Count('invoices', filter=Q(invoices__paid=False))
    )
    return render(request, 'student_list.html', {'students': students})

@login_required
def set_price(request, student_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        try:
            price = Decimal(request.POST.get('price'))
            if price < 0:
                raise ValueError("Price must be a positive number.")
        except (TypeError, ValueError, Decimal.InvalidOperation):
            return HttpResponseBadRequest("Invalid price value.")
        
        lessons = Lesson.objects.filter(student=student, invoice__isnull=True)
        if lessons.exists():
            lessons.update(price=price)
            messages.success(request, f"Price for {student.UserID.first_name} updated successfully.")
        else:
            return HttpResponse("No uninvoiced lessons found for this student.")
    return redirect(f"{reverse('dashboard')}?tab=students")

@login_required
def create_invoice(request, student_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    student = get_object_or_404(Student, id=student_id)
    # Fetch lessons not yet invoiced
    lessons = Lesson.objects.filter(student=student, invoice__isnull=True)
    tutor = None
    if lessons.exists():
        tutor = lessons.first().tutor
    else:
        messages.error(request, "No lessons to invoice for this student.")
        return redirect('student_list')
    total_amount = lessons.count() * lessons.first().price

    if request.method == 'POST':
        # Create the invoice
        invoice = Invoice.objects.create(
            student=student,
            tutor=tutor,
            paid=False,
            total_amount = 0.0,
        )
        for lesson in lessons:
            lesson.invoice = invoice
            lesson.save()
            
        invoice.calculate_total_amount()
        messages.success(request, f"Invoice {invoice.id} created for {student.UserID.full_name()}.")
        return redirect('invoice_detail', invoice_id=invoice.id)

    return render(request, 'create_invoice.html', {
        'student': student,
        'lessons': lessons,
        'total_amount':total_amount
    })
    


@login_required
def invoice_detail(request, invoice_id):
    # Access Control
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.user.role == 'student':
        if request.user != invoice.student.UserID:
            return redirect('dashboard')
    elif request.user.role == 'admin':
        # Admins can view any invoice
        pass
    else:
        # Other roles are not allowed
        return redirect('dashboard')
    
    lessons = Lesson.objects.filter(invoice=invoice)

    
    return render(request, 'invoice_details.html', {'invoice': invoice , 'lessons': lessons})


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

@login_required
def manage_languages(request):
    """View to implement fuzzy and filtering for search to add languages and logic for removing with cleaning orphans."""

    if not request.user.is_authenticated or not hasattr(request.user, 'tutor_profile'):
        messages.warning(request, "You must be a tutor to manage languages.")
        return redirect(reverse('dashboard'))
    
    tutor = request.user.tutor_profile
    query = request.GET.get('query', '').strip()
    languages = tutor.languages.all() 
    search_results = Language.objects.none()
    
    add_form = TutorLanguageForm(initial_query=query)
    remove_form = RemoveLanguageForm(tutor=tutor)
    if query:

        existing_languages = list(Language.objects.values_list('name', flat=True))
        close_matches = get_close_matches(query, existing_languages, n=5, cutoff=0.4)  # Adjust cutoff for similarity
        
  
        search_results = Language.objects.filter(
            Q(name__icontains=query) | Q(name__in=close_matches)
        ).exclude(id__in=languages)

        
        if not search_results.exists():
            new_language, created = Language.objects.get_or_create(name=query)
            tutor.languages.add(new_language)
            if created:
                messages.success(request, f"New language '{new_language.name}' created and added to your languages.")
            else:
                messages.info(request, f"Language '{new_language.name}' already exists and has been added to your languages.")
    
    if request.method == "POST":
        if 'add_language' in request.POST:
            language_name = request.POST.get('language_name', '').strip()
            if language_name:
                language, created = Language.objects.get_or_create(name=language_name)
                tutor.languages.add(language)
                if created:
                    messages.success(request, f"New language '{language.name}' created and added to your languages.")
                else:
                    messages.success(request, f"Language '{language.name}' added to your languages.")
            else:
                add_form = TutorLanguageForm(request.POST, initial_query=query)
                if add_form.is_valid():
                    language = add_form.save_or_create_language()
                    if language:
                        tutor.languages.add(language)
                        messages.success(request, f"{language.name} has been added to your languages.")
                    else:
                        messages.error(request, "Failed to add the language. Please try again.")
                else:
                    messages.error(request, "Invalid input. Please check your form and try again.")


        elif 'remove_language' in request.POST:
            remove_form = RemoveLanguageForm(request.POST, tutor=tutor)
            if remove_form.is_valid():
                language = remove_form.cleaned_data['language_id']
                tutor.languages.remove(language)
                messages.success(request, f"{language.name} has been removed.")

                # Delete language if no tutors are associated
                if language.taught_by.count() == 0:
                    language.delete()
                    messages.info(request, f"{language.name} has been deleted as no tutors teach it anymore.")
            else:
                messages.error(request, "An error occurred while removing the language.")


        

    return render(request, "manage_languages.html", {
        'query': query,
        'languages': languages,
        'add_form': add_form,
        'remove_form': remove_form,
        'search_results': search_results,})

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
    success_url = reverse_lazy('view_request') 

    def form_valid(self, form):
        """attach the logged-in student to the form before saving."""
        try:
            student = self.request.user.student_profile  
        except Student.DoesNotExist:
            return redirect('dashboard')
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

class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'send_message.html'
    success_url = reverse_lazy('all_messages')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reply_id = self.kwargs.get('reply_id')
        if reply_id:
            reply_message = get_object_or_404(Message, pk=reply_id)
            context['reply_message'] = reply_message
        return context
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        reply_id = self.kwargs.get('reply_id')
        if reply_id:
            reply = get_object_or_404(Message, pk=reply_id)
            kwargs['previous_message'] = reply
        return kwargs

    def form_valid(self, form):
        
        form.instance.sender = self.request.user
        messages.success(self.request, "Message sent successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        
        messages.error(self.request, "Failed to send the message. Please correct the errors.")
        return super().form_invalid(form)


class AllMessagesView(LoginRequiredMixin, TemplateView):
    """display all sent and received messages."""
    template_name = 'all_messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['sent_messages'] = user.sent_messages.all().order_by('-created_at')
        context['received_messages'] = user.received_messages.all().order_by('-created_at')
        
        return context

class MessageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """ single message """
    model = Message
    template_name = 'message_detail.html'
    context_object_name = 'message'

    def test_func(self):
        """ensure the user is authorized"""
        message = self.get_object()
        return self.request.user == message.sender or self.request.user == message.recipient
    def get_context_data(self, **kwargs):
        """Add previous message, next message (reply), and reply URL to the context."""
        context = super().get_context_data(**kwargs)
        message = self.get_object()

        
        context['previous_message'] = message.previous_message 
        context['next_message'] = message.reply

        
        context['reply_url'] = reverse('reply_message', kwargs={'reply_id': message.id})

        return context
        
class StudentRequestProcessingView(LoginRequiredMixin, View):
    """View for processing student requests."""
    today = date.today()
    current_year = today.year

    # Define fixed months and days for each term
    TERM_RANGES = {
        'sept-christmas': (
            date(current_year + 1 if today >= date(current_year, 9, 1) else current_year, 9, 1),
            date(current_year + 1 if today >= date(current_year, 9, 1) else current_year, 12, 25),
        ),
        'jan-easter': (
            date(current_year + 1 if today >= date(current_year, 1, 1) else current_year, 1, 1),
            date(current_year + 1 if today >= date(current_year, 1, 1) else current_year, 4, 12),
        ),
        'may-july': (
            date(current_year + 1 if today >= date(current_year, 5, 1) else current_year, 5, 1),
            date(current_year + 1 if today >= date(current_year, 5, 1) else current_year, 7, 31),
        ),
    }

    FREQUENCY_TO_DAYS = {
        'once a week': 7,
        'once per fortnight': 14,
    }

    def get(self, request, request_id):
        """Display the form for processing a student request."""
        student_request = get_object_or_404(StudentRequest, id=request_id)
        form = StudentRequestProcessingForm(student_request=student_request)

        return render(request, 'process_request.html', {
            'form': form,
            'request': student_request,
        })

    def post(self, request, request_id):
        """Handle the form submission for processing a student request."""
        student_request = get_object_or_404(StudentRequest, id=request_id)
        form = StudentRequestProcessingForm(request.POST, student_request=student_request)

        if form.is_valid():
            return self._handle_request_processing(request, form, student_request)

        messages.error(request, "There was an error processing the request. Please try again.")
        return render(request, 'process_request.html', {
            'form': form,
            'request': student_request,
        })

    def _handle_request_processing(self, request, form, student_request):
        """Process the student request based on the form data."""
        status = form.cleaned_data['status']
        details = form.cleaned_data.get('details', '')
        tutor = form.cleaned_data['tutor']
        first_lesson_date = form.cleaned_data['first_lesson_date']
        first_lesson_time = form.cleaned_data['first_lesson_time']

        if status == 'accepted':
            self._process_accepted_request(
                request, student_request, tutor, first_lesson_date, first_lesson_time
            )
        else:
            self._process_denied_request(request, student_request, details)

        student_request.save()
        return redirect('dashboard')

    def _process_accepted_request(self, request, student_request, tutor, first_lesson_date, first_lesson_time):
        """Handle logic for accepted student requests."""
        first_lesson_datetime = datetime.combine(first_lesson_date, first_lesson_time)
        frequency = student_request.frequency
        term = student_request.term
        duration = student_request.duration
        venue = student_request.venue
        term_start, term_end = self.TERM_RANGES.get(term, (None, None))

        scheduled_lessons = self.schedule_lessons_for_term(
            tutor, student_request.student, student_request.language,
            first_lesson_datetime, frequency, duration, term_start, term_end, venue, request
        )

        if scheduled_lessons:
            messages.success(request, f"Request accepted! {len(scheduled_lessons)} lessons have been scheduled.")
            student_request.is_allocated = True
        else:
            messages.error(request, "Unable to schedule lessons due to conflicts.")

    def _process_denied_request(self, request, student_request, details):
        """Handle logic for denied student requests."""
        student_request.is_allocated = False
        messages.warning(request, f"Request rejected. {details}")

    def schedule_lessons_for_term(self, tutor, student, language, start_datetime, frequency, duration, term_start, term_end, venue, request):
        """Schedules lessons for the requested term, resolving conflicts dynamically."""
        scheduled_lessons = []
        current_datetime = start_datetime
        days_between_lessons = self.FREQUENCY_TO_DAYS.get(frequency, 7)

        while current_datetime.date() <= term_end:
            if current_datetime.date() >= term_start:
                available_slot = self.find_available_slot(
                    tutor, student, current_datetime.date(), current_datetime.time(), duration
                )
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
                    messages.error(request, f"No available times for {current_datetime.date()}.")

            current_datetime += timedelta(days=days_between_lessons)

        return scheduled_lessons

    def find_available_slot(self, tutor, student, proposed_date, proposed_time, duration, max_days_to_search=7):
        """Finds an available slot for a lesson, resolving conflicts dynamically."""
        day_delta = timedelta(minutes=30)  # Interval to check for free slots
        max_time = time(21, 0)  # End of the available time range (9 PM)
        
        proposed_date = self._parse_to_date(proposed_date)
        proposed_time = self._parse_to_time(proposed_time)

        def get_earliest_start_time(date):
            return time(15, 0) if date.weekday() < 5 else time(10, 0)  # Weekdays start at 3 PM, weekends at 10 AM

        # Generate the list of days to check: proposed day first, then the rest of the week
        days_to_check = self._generate_days_to_check(proposed_date)

        # Check each day for available slots
        for check_date in days_to_check:
            earliest_start = get_earliest_start_time(check_date)

            # Generate and check slots before and after the proposed time
            for slots in (self.generate_time_slots(check_date, earliest_start, proposed_time, day_delta, duration),
                        self.generate_time_slots(check_date, proposed_time, max_time, day_delta, duration)):
                for slot in slots:
                    if self._is_slot_available(slot, tutor, student, duration):
                        return slot

        return None

    def _parse_to_date(self, proposed_date):
        """Parse a string date to a datetime.date object if needed."""
        return datetime.strptime(proposed_date, "%Y-%m-%d").date() if isinstance(proposed_date, str) else proposed_date

    def _parse_to_time(self, proposed_time):
        """Parse a string time to a datetime.time object if needed."""
        return datetime.strptime(proposed_time, "%H:%M").time() if isinstance(proposed_time, str) else proposed_time

    def _generate_days_to_check(self, proposed_date):
        """Generate a list of days to check, starting with the proposed date."""
        start_of_week = proposed_date - timedelta(days=proposed_date.weekday())  # Monday of the week
        return [proposed_date] + [
            start_of_week + timedelta(days=i) for i in range(7) if start_of_week + timedelta(days=i) != proposed_date
        ]

    def _is_slot_available(self, slot, tutor, student, duration):
        """Check if a given slot is available for a lesson."""
        end_time = (slot + timedelta(minutes=duration)).time()

        if not TutorAvailability.objects.filter(
            tutor=tutor,
            day=slot.date(),
            availability_status='available',
            start_time__lte=slot.time(),
            end_time__gte=end_time
        ).exists():
            return False

        return not self._has_conflicts(slot, student, tutor, duration)

    def _has_conflicts(self, slot, student, tutor, duration):
        """Check if the slot conflicts with existing lessons."""
        end_time = (slot + timedelta(minutes=duration)).time()

        def conflicts_with_lessons(lessons):
            for lesson in lessons:
                lesson_end_time = (datetime.combine(lesson.date, lesson.time) + timedelta(minutes=lesson.duration)).time()
                if (
                    (slot.time() < lesson_end_time and end_time > lesson.time) or  # New starts before, ends after
                    (slot.time() < lesson.time and end_time > lesson.time and end_time <= lesson_end_time) or  # New starts before, ends during
                    (slot.time() >= lesson.time and slot.time() < lesson_end_time and end_time <= lesson_end_time) or  # New starts during, ends during
                    (slot.time() >= lesson.time and slot.time() < lesson_end_time and end_time > lesson_end_time)  # New starts during, ends after
                ):
                    return True
            return False

        student_lessons = Lesson.objects.filter(student=student, date=slot.date())
        tutor_lessons = Lesson.objects.filter(tutor=tutor, date=slot.date())

        return conflicts_with_lessons(student_lessons) or conflicts_with_lessons(tutor_lessons)

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
        form = LessonUpdateForm(instance=lesson)

        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})

    def post(self, request, lesson_id):
        """Handle the form submission for changing or cancelling a lesson."""

        lesson = get_object_or_404(Lesson, id=lesson_id)
        form = LessonUpdateForm(request.POST, instance=lesson)

        if form.is_valid():
            if self._is_cancellation_requested(form):
                return self._handle_cancellation(request, lesson)

            return self._handle_update(request, form, lesson)

        # If the form is invalid
        messages.error(request, "There was an error updating the lesson. Please try again.")
        return render(request, 'lesson_update.html', {'form': form, 'lesson': lesson})

    def _is_cancellation_requested(self, form):
        """Determine if the cancellation checkbox is selected."""

        return form.cleaned_data.get('cancel_lesson', False)

    def _handle_cancellation(self, request, lesson):
        """Handle cancellation logic: delete the lesson and redirect."""
        
        lesson.delete()

        messages.success(request, "Lesson successfully cancelled.")
        return redirect('dashboard')

    def _handle_update(self, request, form, lesson):
        """Handle lesson rescheduling logic: save the updated date/time."""
        
        lesson.date = form.cleaned_data['new_date']
        lesson.time = form.cleaned_data['new_time']
        lesson.save()

        messages.success(request, "Lesson details successfully updated.")
        return redirect('dashboard')

    
class TutorAvailabilityView(LoginRequiredMixin, View):
    """View for tutors to manage availability requests."""
    model = TutorAvailability
    template = 'tutor_availability_request.html'

    def get(self, request, availability_id=None):
        try:
            tutor = Tutor.objects.get(UserID=request.user)
        except Tutor.DoesNotExist:
            return redirect("dashboard")
        
        availabilities = TutorAvailability.objects.filter(tutor=tutor)

        if availability_id:
            action = request.GET.get('action')
            if action == 'edit':
                availability = get_object_or_404(TutorAvailability, id=availability_id, tutor=tutor)
                form = TutorAvailabilityForm(instance=availability)
            elif action == 'delete':
                availability = get_object_or_404(TutorAvailability, id=availability_id, tutor=tutor)
                availability.delete()
                return redirect(f"{reverse('dashboard')}?tab=availability")
            else:
                return HttpResponseBadRequest("Invalid action.")
        else:
            form = TutorAvailabilityForm(initial={'tutor': tutor})

        context = {
            "tutor": tutor,
            "availabilities": availabilities,
            "form": form,
        }
        return render(request, self.template, context)

    @staticmethod
    def has_overlapping(tutor, day, new_start, new_end):
        return TutorAvailability.objects.filter(
            tutor=tutor,
            day=day,
            start_time__lt=new_end,
            end_time__gt=new_start
        ).exists()

    def post(self, request, availability_id=None):
        try:
            tutor = Tutor.objects.get(UserID=request.user)
        except Tutor.DoesNotExist:
            return redirect(f"{reverse('dashboard')}?tab=availability")

        if availability_id:
            availability = get_object_or_404(TutorAvailability, id=availability_id, tutor=tutor)
            form = TutorAvailabilityForm(request.POST, instance=availability)
        else:
            form = TutorAvailabilityForm(request.POST, initial={'tutor': Tutor.objects.get(UserID=request.user)})

        if form.is_valid():
            print("Form is valid")
            new_availability = form.save(commit=False)
            new_availability.tutor = tutor
            day = form.cleaned_data['day']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            if self.has_overlapping(tutor, day, start_time, end_time):
                form.add_error(None, "This time slot overlaps with an existing availability.")
                availabilities = TutorAvailability.objects.filter(tutor=tutor)
                return render(request, self.template, {
                    "tutor": tutor,
                    "availabilities": availabilities,
                    "form": form,
                })

            new_availability.save()
            return redirect(f"{reverse('dashboard')}?tab=availability")
        print("Form is not valid")
        print(form.errors)
        availabilities = TutorAvailability.objects.filter(tutor=tutor)
        return render(request, self.template, {
            "tutor": tutor,
            "availabilities": availabilities,
            "form": form,
        })